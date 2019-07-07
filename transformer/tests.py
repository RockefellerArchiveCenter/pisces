import json
import os
import random
import vcr

from django.test import Client, TestCase
from django.urls import reverse
from odin.codecs import json_codec

from .test_library import import_fixture_data, add_wikidata_ids, add_wikipedia_ids, get_random_string
from .resources import *
from .fetchers import *
from .transformers import *

fetch_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

AS_TYPE_MAP = [('agent_corporate_entity', ArchivesSpaceAgentCorporateEntity),
               ('agent_family', ArchivesSpaceAgentFamily),
               ('agent_person', ArchivesSpaceAgentPerson),
               ('archival_objects', ArchivesSpaceArchivalObject),
               ('resources', ArchivesSpaceResource),
               ('subjects', ArchivesSpaceSubject)]


class TransformerTest(TestCase):

    def test_as_resources(self):
        for resource in AS_TYPE_MAP:
            for f in os.listdir(os.path.join('fixtures', resource[0])):
                with open(os.path.join('fixtures', resource[0], f), 'r') as json_file:
                    obj = json_codec.load(json_file, resource=resource[1])
