import json
import os

import vcr
from django.test import TestCase
from jsonschema import validate
from pisces import settings

from .resources import (Agent, ArchivesSpaceAgentCorporateEntity,
                        ArchivesSpaceAgentFamily, ArchivesSpaceAgentPerson,
                        ArchivesSpaceArchivalObject, ArchivesSpaceResource,
                        ArchivesSpaceSubject, Collection, Object, Term)
from .transformers import ArchivesSpaceDataTransformer

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
    """
    Tests the transformations and mappings against the RAC data model schema.
    Opens the JSON schema and then runs the transformations against every file
    in the directories included in the AS_TYPE_MAP. Validates against the correct
    type in the data model and then provides an error if the validation fails.
    """

    def test_as_mappings(self):
        with open(os.path.join(settings.BASE_DIR, 'rac-data-model', 'schema.json')) as sf:
            schema = json.load(sf)
            for resource in AS_TYPE_MAP:
                with fetch_vcr.use_cassette("{}.json".format(resource[0])):
                    for f in os.listdir(os.path.join('fixtures', resource[0])):
                        with open(os.path.join('fixtures', resource[0], f), 'r') as json_file:
                            transform = ArchivesSpaceDataTransformer().run(json.load(json_file))
                            self.assertNotEqual(transform, False)
                            valid = validate(instance=json.loads(transform), schema=schema)
                            self.assertEqual(valid, None)
