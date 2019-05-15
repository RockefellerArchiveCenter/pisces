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
            for s in self.repo.subjects.with_params(all_ids=True, modified_since=self.last_run): #Not sure this will work, but want to work out general logic first
                if s.publish:
                    self.save_data(Term, 'term', s) # a little unsure about this line

    def get_agents(self):
            for a in self.repo.agents["people"].with_params(all_ids=True, modified_since=self.last_run): #definitely sketchy, just want some logic here
                if a.publish:
                    self.save_data(Agent, 'agent', a)
            for a in self.repo.agents["corporate_entities"].with_params(all_ids=True, modified_since=self.last_run):
                if a.publish:
                    self.save_data(Agent, 'agent', a)
            for a in self.repo.agents["families"].with_params(all_ids=True, modified_since=self.last_run):
                if a.publish:
                    self.save_data(Agent, 'agent', a)
            for a in self.repo.agents["software"].with_params(all_ids=True, modified_since=self.last_run):
                if a.publish:
                    self.save_data(Agent, 'agent', a)

    def get_objects(self):
        for o in self.repo.archival_objects.with_params(all_ids=True, modified_since=self.last_run):
            r = o.resource
            resource_id = o.get('resource').get('ref').split('/')[-1]
            with open(os.path.join(settings.BASE_DIR, source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
                tree_data = json.load(tf)
                full_tree = objectpath.Tree(tree_data)
                partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(data.get('uri')))
                # Save archival object as Collection if it has children, otherwise save as Object
                # Tree.execute() is a generator function so we have to loop through the results
                for p in partial_tree:
                    if p.get('has_children'):
                        collections_check()
                    else:
                        objects_check()
            if r.publish and o.publish:
                pass

    #objects function
    def objects_check(self):
        if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref).exists():
            new_object = Object.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref)
            sd = SourceData.objects.get(object=new_object)
            sd.data = p.json
            sd.save()
        else:
            object = Obect.objects.create(source=Identifier.ARCHIVESSPACE, data=p.json)
            Identifier.objects.create(object=object, source=Identifier.ARCHIVESSPACE, identifier=p.ref)
            SourceData.objects.create(object=object, source=Identifier.ARCHIVESSPACE, data=p.json)

    #objects function
    def collections_check(self):
        if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=r.ref).exists():
            new_object = Collection.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=r.ref)
            sd = SourceData.objects.get(collection=new_object)
            sd.data = r.json
            sd.save()
        else:
            collection = Collection.objects.create(source=Identifier.ARCHIVESSPACE, data=r.json)
            Identifier.objects.create(collection=collection, source=Identifier.ARCHIVESSPACE, identifier=r.ref)
            SourceData.objects.create(collection=collection, source=Identifier.ARCHIVESSPACE, data=r.json)

    #terms function
    def term_check(self):
        if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=s.ref).exists():
            new_object = Term.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=s.ref)
            sd = SourceData.objects.get(term=new_object)
            sd.data = s.json
            sd.save()
        else:
            term = Term.objects.create(source=Identifier.ARCHIVESSPACE, data=s.json)
            Identifier.objects.create(term=term, source=Identifier.ARCHIVESSPACE, identifier=s.ref)
            SourceData.objects.create(term=term, source=Identifier.ARCHIVESSPACE, data=s.json)

    #agents function
    def agent_check(self):
        if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref).exists():
            new_object = Agent.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref)
            sd = SourceData.objects.get(agent=new_object)
            sd.data = a.json
            sd.save()
        else:
            agent = Agent.objects.create(source=Identifier.ARCHIVESSPACE, data=a.json)
            Identifier.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, identifier=a.ref)
            SourceData.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, data=a.json)

    # Generic function to save data.
    def save_data(self, cls, key, data, source_tree=None):
        if cls.objects.filter(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=data.uri).exists():
            object = cls.objects.get(identifier__source=Identifier.ARCHIVESSPACE, identifier__identifier=data.uri)
            if source_tree:
                object.source_tree = source_tree.json()
                object.save()
            source_data = SourceData.objects.get(**{key: object, "source": Identifier.ARCHIVESSPACE})
            source_data.data = data._json
            source_data.save()
        else:
            object = cls.objects.create(source_tree=source_tree._json) if source_tree else cls.objects.create()
            Identifier.objects.create(**{key: object, "source": Identifier.ARCHIVESSPACE, "identifier": data.uri})
            SourceData.objects.create(**{key: object, "source": Identifier.ARCHIVESSPACE, "data": data._json})


class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()

    def run(self):
        for agent in Agent.objects.filter(wikidata_id__isnull=False):
            print(agent)
            agent_data = self.client.get(agent.wikidata_id, load=True).data
            if SourceData.objects.filter(source=SourceData.WIKIDATA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent)
                # Could insert a check here to see if data has been updated since last save.
                source_data.data = agent_data
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIDATA, data=agent_data, agent=agent)
            if not Identifier.objects.filter(source=Identifier.WIKIDATA, agent=agent).exists():
                Identifier.objects.create(source=Identifier.WIKIDATA, identifier=agent.wikidata_id, agent=agent)


class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')

    def run(self):
        for agent in Agent.objects.filter(wikipedia_url__isnull=False):
            agent_name = agent.wikipedia_url.split('/')[-1]
            print(agent)
            agent_page = self.client.page(agent_name)
            if SourceData.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                source_data = SourceData.objects.get(source=SourceData.WIKIPEDIA, agent=agent)
                source_data.data = agent_page.summary
                source_data.save()
            else:
                SourceData.objects.create(source=SourceData.WIKIPEDIA, data=agent_page.summary, agent=agent)
            if not Identifier.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                # TODO: Something is happening to agent_name in the save that is stripping spaces and truncating, etc.
                # Maybe get a better identifier?
                Identifier.objects.create(source=Identifier.WIKIPEDIA, identifier=agent_name, agent=agent)
