import os
import json

from asnake.aspace import ASpace
from wikipediaapi import Wikipedia
from wikidata.client import Client as wd_client

from .models import *


class ArchivesSpaceDataFetcher:
    def __init__(self, object_type):
        self.aspace = ASpace(
                      baseurl='http://192.168.50.4:8089',
                      user='admin',
                      password='admin')
        self.repo = self.aspace.repositories(2)
        self.last_run = (FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=object_type).order_by('-start_time')[0].start_time.timestamp()
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=object_type).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.ARCHIVESSPACE, object_type=object_type)
        self.object_type = object_type

    def run(self):
        getattr(self, "get_{}".format(self.object_type))()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()

    def get_resources(self):
            for r in self.repo.resources.with_params(all_ids=True, modified_since=self.last_run):
                if (r.publish and r.id_0.startswith('FA')):
                        tree = self.aspace.client.get(r.tree.ref)  # Is there a better way to do this?
                        self.save_data(Collection, 'collection', r, tree) #Not exactly sure how this is working

    def get_subjects(self):
            for s in self.aspace.subjects.with_params(all_ids=True, modified_since=self.last_run): #Not sure this will work, but want to work out general logic first
                if s.publish:
                    self.save_data(Term, 'term', s) # a little unsure about this line

    def get_agents(self):
        for agent_type in ["people", "corporate_entities", "families", "software"]:
            for a in self.aspace.agents[agent_type].with_params(all_ids=True, modified_since=self.last_run): #definitely sketchy, just want some logic here
                if a.publish:
                    self.save_data(Agent, 'agent', a)

    def get_objects(self):
        for o in self.repo.archival_objects.with_params(all_ids=True, modified_since=self.last_run):
            if o.publish:
                r = o.resource
                tree_data = self.aspace.client.get(r.tree.ref).json()
                full_tree = objectpath.Tree(tree_data)
                partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(data.get('uri')))
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
                object.source_tree = source_tree.json()
                object.save()
            source_data = SourceData.objects.get(**{relation_key: object, "source": Identifier.ARCHIVESSPACE})
            source_data.data = data._json
            source_data.save()
        else:
            object = cls.objects.create(source_tree=source_tree.json()) if source_tree else cls.objects.create()
            Identifier.objects.create(**{relation_key: object, "source": Identifier.ARCHIVESSPACE, "identifier": data.uri})
            SourceData.objects.create(**{relation_key: object, "source": Identifier.ARCHIVESSPACE, "data": data._json})


class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIDATA)

    def run(self):
        self.get_agents()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIDATA):
            print(agent)
            wikidata_id = Identifier.objects.filter(source=Identifier.WIKIDATA, agent=agent).identifier
            agent_data = self.client.get(wikidata_id, load=True).data
            if SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent)
                source_data.data = agent_data
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIDATA, data=agent_data, agent=agent)


class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIPEDIA)

    def run(self):
        self.get_agents()
        self.current_run.status = TransformRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIPEDIA):
            wikipedia_id = Identifier.objects.get(source=WIKIPEDIA, agent=agent)
            agent_page = self.client.page(wikipedia_id)
            if SourceData.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIPEDIA, agent=agent)
                source_data.data = agent_page.summary
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIPEDIA, data=agent_page.summary, agent=agent)
