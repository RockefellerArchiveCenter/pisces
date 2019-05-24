import os
import objectpath
import json
import requests

from asnake.aspace import ASpace
from django.utils import timezone
from wikipediaapi import Wikipedia
from wikidata.client import Client as wd_client
from electronbonder.client import ElectronBond

from .models import *
from pisces import settings


class ArchivesSpaceDataFetcherError(Exception): pass


class ArchivesSpaceDataFetcher:
    def __init__(self, object_type=None, target=None):
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             user=settings.ARCHIVESSPACE['user'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=object_type).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=object_type).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.ARCHIVESSPACE, object_type=object_type)
        if object_type in ['resources', 'subjects', 'agents', 'objects', None]:
            self.object_types = [object_type] if object_type else ['resources', 'subjects', 'agents', 'objects']
        else:
            raise ArchivesSpaceDataFetcherError("Unknown object type {}".format(object_type))
        if target in ['updated', 'deleted', None]:
            self.targets = [target] if target else ['updated', 'deleted']
        else:
            raise ArchivesSpaceDataFetcherError("Unknown target {}".format(target))

    def run(self):
        for target in self.targets:
            getattr(self, "get_{}".format(target))()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_deleted(self):
        try:
            deletions = self.aspace.client.get_paged("delete-feed", params={"modified_since": str(self.last_run)})
            for d in deletions:
                if "agents/" in d:
                    self.delete_data(Agent, d)
                elif "subjects/" in d:
                    self.delete_data(Term, d)
                elif "archival_objects/" in d:
                    self.delete_data(Object, d)
                    self.delete_data(Collection, d)
                elif "resources/" in d:
                    self.delete_data(Collection, d)
        except Exception as e:
            print(e)
            FetchRunError.objects.create(run=self.current_run, message="Error fetching deleted ArchivesSpace data: {}".format(e))

    def get_updated(self):
        try:
            for object_type in self.object_types:
                getattr(self, "get_{}".format(object_type))()
        except Exception as e:
            FetchRunError.objects.create(run=self.current_run, message="Error fetching updated ArchivesSpace data: {}".format(e))

    def get_resources(self):
        for r in self.repo.resources.with_params(all_ids=True, modified_since=self.last_run):
            if (r.publish and r.id_0.startswith('FA')):
                    tree = self.aspace.client.get(r.tree.ref)  # Is there a better way to do this?
                    self.save_data(Collection, 'collection', r, tree.json())

    def get_subjects(self):
        for s in self.aspace.subjects.with_params(all_ids=True, modified_since=self.last_run):
            if s.publish:
                self.save_data(Term, 'term', s)

    def get_agents(self):
        for agent_type in ["people", "corporate_entities", "families", "software"]:
            for a in self.aspace.agents[agent_type].with_params(all_ids=True, modified_since=self.last_run):
                if a.json().get('publish'):  # this seems like an ASnake bug
                    self.save_data(Agent, 'agent', a)

    def get_objects(self):
        for o in self.repo.archival_objects.with_params(all_ids=True, modified_since=self.last_run):
            if o.publish:
                r = o.resource
                tree_data = self.aspace.client.get(r.tree.ref).json()
                full_tree = objectpath.Tree(tree_data)
                partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(o.uri))
                # Save archival object as Collection if it has children, otherwise save as Object
                # Tree.execute() is a generator function so we have to loop through the results
                for p in partial_tree:
                    if p.get('has_children'):
                        self.save_data(Collection, 'collection', o, p)
                    else:
                        self.save_data(Object, 'object', o)

    def save_data(self, cls, relation_key, data, source_tree=None):
        """
        A generic function to save data. Takes the following arguments:
        cls: an instance of a class (Agent, Term, Collection or Object)
        relation_key: a string representation of a relation key for Identifier and SourceData objects
        data: a JSONModel instance of an Agent, Term, Collection or Object
        source_tree (optional): source data tree containing all children of a Collection
        """
        if cls.objects.filter(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=data.uri).exists():
            object = cls.objects.get(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=data.uri)
            if source_tree:
                object.source_tree = source_tree
                object.save()
            source_data = SourceData.objects.get(**{relation_key: object, "source": Identifier.ARCHIVESSPACE})
            source_data.data = data._json
            source_data.save()
        else:
            object = cls.objects.create(source_tree=source_tree) if source_tree else cls.objects.create()
            Identifier.objects.create(**{relation_key: object, "source": Identifier.ARCHIVESSPACE, "identifier": data.uri})
            SourceData.objects.create(**{relation_key: object, "source": Identifier.ARCHIVESSPACE, "data": data._json})

    def delete_data(self, cls, identifier):
        if cls.objects.filter(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=identifier).exists():
            cls.objects.get(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=identifier).delete()


class CartographerDataFetcher:
    def __init__(self):
        self.client = ElectronBond(baseurl=settings.CARTOGRAPHER['baseurl'], user=settings.CARTOGRAPHER['user'], password=settings.CARTOGRAPHER['password'])
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        try:
            resp = self.client.get('/status/')
            if not resp.status_code:
                FetchRunError.objects.create(run=self.current_run, message="Cartographer status endpoint is not available. Service may be down.")
        except Exception as e:
            FetchRunError.objects.create(run=self.current_run, message="Cartographer is not available.")

    def run(self):
        self.get_maps()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_maps(self):
        for map in self.client.get('/api/maps/', params={"updated_since": self.last_run}).json()['results']:
            try:
                m = self.client.get(map.get('url')).json()
                self.process_map_item(m)
            except Exception as e:
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Cartographer map: {}".format(e))

    def process_map_item(self, data):
        identifier = data.get('ref', data.get('url'))
        source = Identifier.ARCHIVESSPACE if 'repositories' in identifier else Identifier.CARTOGRAPHER
        if not Collection.objects.filter(identifier__source=source, identifier__identifier=identifier).exists():
            c = Collection.objects.create(source_tree=data)
            SourceData.objects.create(collection=c, source=SourceData.CARTOGRAPHER, data=data)
            Identifier.objects.create(collection=c, source=source, identifier=identifier)
        if data.get('children'):
            for item in data.get('children'):
                self.process_map_item(item)


class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIDATA)

    def run(self):
        self.get_agents()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIDATA):
            print(agent)
            try:
                wikidata_id = Identifier.objects.get(source=Identifier.WIKIDATA, agent=agent).identifier
                agent_data = self.client.get(wikidata_id, load=True).data
                if SourceData.objects.filter(source=SourceData.WIKIDATA, agent=agent).exists():
                    source_data = SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent)
                    source_data.data = agent_data
                    source_data.save()
                else:
                    SourceData.objects.create(source=SourceData.WIKIDATA, data=agent_data, agent=agent)
            except Exception as e:
                print(e)
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Wikidata data for agent: {}".format(e))


class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIPEDIA)

    def run(self):
        self.get_agents()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIPEDIA):
            try:
                wikipedia_id = Identifier.objects.get(source=Identifier.WIKIPEDIA, agent=agent).identifier
                print(wikipedia_id)
                agent_page = self.client.page(wikipedia_id)
                print(agent_page)
                if SourceData.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                    source_data = SourceData.objects.get(source=SourceData.WIKIPEDIA, agent=agent)
                    source_data.data = agent_page.summary
                    source_data.save()
                else:
                    SourceData.objects.create(source=SourceData.WIKIPEDIA, data=agent_page.summary, agent=agent)
            except Exception as e:
                print(e)
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Wikipedia data for agent: {}".format(e))
