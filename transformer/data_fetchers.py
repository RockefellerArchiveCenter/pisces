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

terms = ['77', '123']

#terms function
for term in terms:
    term_json = aspace.subjects(term).json()
    print(term_json)
    if Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=term.get('ref')).exists():
        new_object = term.objects.get('ref')
        SourceData.objects.get('ref') #not exactly sure what to do here. Don't know what to pass in the get statement
        sd = new_object.sourcedata_set().filter(source) #not sure about what's happening here
        sd.data = term_json
        sd.save()
    else:
        Term.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "data": term_json}) #not sure about the key: obj part
        Identifier.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "identifier": data.get('uri')})
        SourceData.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "data": term_json})

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
