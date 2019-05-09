from dateutil import parser
import os
import json
from asnake.aspace import ASpace
from pycountry import languages
from uuid import uuid4

from django.utils import timezone

from .models import *


class ArchivesSpaceDataFetcher:
    def __init__(self):
        self.aspace = ASpace(
                      baseurl='http://192.168.50.4:8089',
                      user='admin',
                      password='admin')
        self.repo = aspace.repositories(2)

    def get_resources(self):
            for r in aspace.resources.with_params(all_ids=True, modified_since=updated):
                if r.publish:
                    if r.jsonmodel_type == 'resource' and r.id_0.startswith('FA'):
                        collections_check()

    def get_objects(self):
        for o in aspace.archival_objects.with_params(all_ids=True, modified_since=updated):
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

    def get_subjects(self):
            for s in aspace.subjects:
                if s.publish and s.system_mtime > updated:
                    term_check()

    def get_agents(self):
            for a in aspace.agents["people"]:
                if a.publish and a.system_mtime > updated:
                    agent_check()
            for a in aspace.agents["corporate_entities"]:
                if a.publish and a.system_mtime > updated:
                    agent_check()
            for a in aspace.agents["families"]:
                if a.publish and a.system_mtime > updated:
                    agent_check()
            for a in aspace.agents["software"]:
                if a.publish and a.system_mtime > updated:
                    agent_check()

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
