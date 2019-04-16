# Add data fetchers here
from dateutil import parser
import os
import json
from asnake.aspace import ASpace
from pycountry import languages
from uuid import uuid4

from django.utils import timezone

from .models import *


aspace = ASpace(
              baseurl='http://192.168.50.4:8089',
              user='admin',
              password='admin'
              )
repo = aspace.repositories(2)

terms = []

def check_subjects(self, archival=False, library=False, updated=0):
        for s in self.repo.subjects.with_params(all_ids=True, modified_since=updated):
            if s.publish:
                terms.append(s['ref'])
            else:
                pass

#terms function
def term_check()
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
def agent_check()
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref.exists():
        new_object = Agent.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=a.ref)
        sd = SourceData.objects.get(agent=new_object)
        sd.data = a.json
        sd.save()
    else:
        agent = Agent.objects.create(source=Identifier.ARCHIVESSPACE, data=a.json)
        Identifier.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, identifier=a.ref)
        SourceData.objects.create(agent=agent, source=Identifier.ARCHIVESSPACE, data=a.json)

#LOGIC
#Get all archival objects, resources, agents, terms updated in the last hour
    #For each updated archival object, agent, term, resource
        #set term.json to a variable
        #get ref
            #Check to see if id exists in database
                #if exists
                    #get object from database
                    #set object to new object variable
                    #get source data
                    #set source data to nobj.sourcedata_set().filter(source) - this is checking for a matching foreign key in the source data
                    #set sd.data to term.json (set the source data section to the updated exported json)
                    #sd.save() save the updated data
                #if doesn't exists
                    #create the object
                    #create Identifier(object=ob)
                    #create SourceData(object=ob)
#Separate steps for AO. Tackle in future.
                #Find ref for the resource (this should be the same as the tree id)
                #Use that ref to grab the tree JSON
                #Store the tree data
                    #With tree data open
                    #GET CHILDREN & PARENTS
                    #USE THE TREE JSON to search for the object ID
                        #When you find the correct ID
                            #Check for children
                                #If you find children, store them to a list
                                #If you don't find children, don't do anything
                            #Go back up tree to find parents and ancestors
                                #Store them to a list
                #Check if object already exists in the database
