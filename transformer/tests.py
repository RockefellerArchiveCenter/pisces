import json
import os
import vcr

from jsonschema import validate

from django.test import TestCase

from .resources import Agent, Collection, Object, Term, ArchivesSpaceAgentPerson, ArchivesSpaceAgentCorporateEntity, ArchivesSpaceAgentFamily, ArchivesSpaceResource, ArchivesSpaceArchivalObject, ArchivesSpaceSubject
from .transformers import ArchivesSpaceDataTransformer
from pisces import settings

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
