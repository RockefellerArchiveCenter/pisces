import json
import os
import random
import vcr

from jsonschema import validate, exceptions

from django.test import Client, TestCase
from django.urls import reverse
from odin.codecs import json_codec

from .fetchers import *
from .resources import *
from .test_library import import_fixture_data, add_wikidata_ids, add_wikipedia_ids, get_random_string
from .transformers import *

fetch_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

AS_TYPE_MAP = [('agent_corporate_entity', ArchivesSpaceAgentCorporateEntity, Agent),
               ('agent_family', ArchivesSpaceAgentFamily, Agent),
               ('agent_person', ArchivesSpaceAgentPerson, Agent),
               ('archival_objects', ArchivesSpaceArchivalObject, Object),
               ('resources', ArchivesSpaceResource, Collection),
               ('subjects', ArchivesSpaceSubject, Term)]


class TransformerTest(TestCase):

    #def test_as_resources(self):
        #for resource in AS_TYPE_MAP:
            #for f in os.listdir(os.path.join('fixtures', resource[0])):
                #with open(os.path.join('fixtures', resource[0], f), 'r') as json_file:
                    #obj = json_codec.load(json_file, resource=resource[1])
                    #self.assertNotEqual(obj, False)

    def test_as_mappings(self):
        with open(os.path.join(settings.BASE_DIR, 'rac-data-model', 'schema.json')) as sf:
            schema = json.load(sf)
            for resource in AS_TYPE_MAP:
                with fetch_vcr.use_cassette("{}.json".format(resource[0])):
                    for f in os.listdir(os.path.join('fixtures', resource[0])):
                        print(f)
                        with open(os.path.join('fixtures', resource[0], f), 'r') as json_file:
                            transform = ArchivesSpaceDataTransformer().run(json.load(json_file))
                            print(transform)
                            self.assertNotEqual(transform, False)
                            valid = validate(instance=json.loads(transform), schema=schema)
                            self.assertEqual(valid, None)
