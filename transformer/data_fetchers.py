# Add data fetchers here
#from dateutil import parser
import os
import json
from asnake.aspace import ASpace
#from pycountry import languages
#from uuid import uuid4

#from django.utils import timezone

#from .models import *


aspace = ASpace(
              baseurl='http://192.168.50.4:8089',
              user='admin',
              password='admin'
              )
repo = aspace.repositories(2)

terms = []

def check_subjects(self, archival=False, library=False, updated=0):
        for s in aspace.subjects:
            if s.publish:
                term_check()
            else:
                pass

def check_agents():
        #for a in self.repo.agents.with_params(all_ids=True, modified_since=updated):
        for a in aspace.agents["people"]:
            print(a.uri)
            #if a.publish:
                #agent_check()
            #else:
                #pass

with open(os.path.join(settings.BASE_DIR, source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
    tree_data = json.load(tf)
    full_tree = objectpath.Tree(tree_data)
    partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(data.get('uri')))
    # Save archival object as Collection if it has children, otherwise save as Object
    # Tree.execute() is a generator function so we have to loop through the results
        for p in partial_tree:
            if p.get('has_children'):
                pass
            else:
                pass

#objects function
def objects_check():
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref.exists():
        new_object = Object.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref)
        sd = SourceData.objects.get(object=new_object)
        sd.data = p.json
        sd.save()
    else:
        object = Obect.objects.create(source=Identifier.ARCHIVESSPACE, data=p.json)
        Identifier.objects.create(object=object, source=Identifier.ARCHIVESSPACE, identifier=p.ref)
        SourceData.objects.create(object=object, source=Identifier.ARCHIVESSPACE, data=p.json)

#objects function
def collections_check():
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref.exists():
        new_object = Collection.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=p.ref)
        sd = SourceData.objects.get(collection=new_object)
        sd.data = p.json
        sd.save()
    else:
        collection = Collection.objects.create(source=Identifier.ARCHIVESSPACE, data=p.json)
        Identifier.objects.create(collection=collection, source=Identifier.ARCHIVESSPACE, identifier=p.ref)
        SourceData.objects.create(collection=collection, source=Identifier.ARCHIVESSPACE, data=p.json)

#terms function
def term_check():
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=s.ref.exists():
        new_object = Term.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=s.ref)
        sd = SourceData.objects.get(term=new_object)
        sd.data = s.json
        sd.save()
    else:
        term = Term.objects.create(source=Identifier.ARCHIVESSPACE, data=s.json)
        Identifier.objects.create(term=term, source=Identifier.ARCHIVESSPACE, identifier=s.ref)
        SourceData.objects.create(term=term, source=Identifier.ARCHIVESSPACE, data=s.json)

#agents function
def agent_check():
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref.exists():
        new_object = Agent.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref)
        sd = SourceData.objects.get(agent=new_object)
        sd.data = a.json
        sd.save()
    else:
        agent = Agent.objects.create(source=Identifier.ARCHIVESSPACE, data=a.json)
        Identifier.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, identifier=a.ref)
        SourceData.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, data=a.json)
