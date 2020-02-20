import json
import os

import vcr
from django.test import TestCase
from jsonschema import validate
from pisces import settings

from .transformers import ArchivesSpaceDataTransformer

fetch_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

object_types = ['agent_corporate_entity', 'agent_family', 'agent_person',
                'archival_objects', 'resources', 'subjects']


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
            for object in object_types:
                with fetch_vcr.use_cassette("{}.json".format(object)):
                    for f in os.listdir(os.path.join('fixtures', object)):
                        with open(os.path.join('fixtures', object, f), 'r') as json_file:
                            source = json.load(json_file)
                            transform = ArchivesSpaceDataTransformer().run(source)
                            self.assertNotEqual(transform, False, "Transformer returned an error: {}".format(transform))
                            transformed = json.loads(transform)
                            valid = validate(instance=transformed, schema=schema)
                            self.assertEqual(valid, None, "Transformed object was not valid: {}".format(valid))
                            self.check_list_counts(source, transformed, object)
                            self.check_agent_counts(source, transformed)

    def check_list_counts(self, source, transformed, object_type):
        """
        Check that lists of items are the same on source and data objects. Since
        transformer logic inherits dates from parent objects in some circumstances,
        the test for these is less stringent and allows for dates on transformed
        objects that do not exist on source objects.
        """
        for source_key, transformed_key in [("notes", "notes"),
                                            ("rights_statements", "rights")]:
            source_len = len(source.get(source_key, ""))
            transformed_len = len(transformed.get(transformed_key, ""))
            self.assertEqual(source_len, transformed_len,
                             "Found {} {} in source but {} {} in transformed.".format(
                                 source_len, source_key, transformed_len, transformed_key
                             ))
        date_source_key = "dates_of_existence" if object_type.startswith("agent_") else "dates"
        for source_key, transformed_key in [(date_source_key, "dates"), ("extents", "extents")]:
            source_len = len(source.get(source_key, ""))
            transformed_len = len(transformed.get(transformed_key, ""))
            self.assertTrue(source_len <= transformed_len,
                            "Incorrect number of {} in transformed source. Found {} but expecting <= {}".format(
                                transformed_key, transformed_len, source_len
                            ))

    def check_agent_counts(self, source, transformed):
        """
        Checks that linked_agents on sources are correctly parsed into creators
        and 'regular' agents.
        """
        source_creator_count = len([obj for obj in source.get("linked_agents", "") if obj.get("role") == "creator"])
        source_agent_count = len([obj for obj in source.get("linked_agents", "") if obj.get("role") != "creator"])
        self.assertEqual(source_creator_count, len(transformed.get("creators", "")))
        self.assertEqual(source_agent_count, len(transformed.get("agents", "")))
