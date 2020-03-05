import json
import os

import vcr
from django.test import TestCase

from .transformers import Transformer

transformer_vcr = vcr.VCR(
    serializer="json",
    cassette_library_dir="fixtures/cassettes/transformer",
    record_mode="once",
    match_on=["path", "method", "query"],
    filter_query_parameters=["username", "password"],
    filter_headers=["Authorization", "X-ArchivesSpace-Session"],
)

object_types = ["agent_corporate_entity", "agent_family", "agent_person",
                "archival_object", "resource", "subject",
                "archival_object_collection"]


# TODO:  update fixtures after mergers have been updated

class TransformerTest(TestCase):
    """
    Tests the transformations and mappings against the RAC data model schema.
    Opens the JSON schema and then runs the transformations against every file
    in the directories included in the AS_TYPE_MAP. Validates against the correct
    type in the data model and then provides an error if the validation fails.
    """

    def test_mappings(self):
        """Tests transformation of source data resources."""
        for object_type in object_types:
            for f in os.listdir(os.path.join("fixtures", "transformer", object_type)):
                with open(os.path.join("fixtures", "transformer", object_type, f), "r") as json_file:
                    source = json.load(json_file)
                    transformed = Transformer().run(object_type, source)
                    self.assertNotEqual(
                        transformed, False,
                        "Transformer returned an error: {}".format(transformed))
                    transformed_data = json.loads(transformed)
                    self.check_list_counts(source, transformed_data, object_type)
                    self.check_agent_counts(source, transformed_data)

    def check_list_counts(self, source, transformed, object_type):
        """Checks that lists of items are the same on source and data objects.

        Since transformer logic inherits dates from parent objects in some
        circumstances, the test for these is less stringent and allows for
        dates on transformed objects that do not exist on source objects.
        """
        date_source_key = "dates_of_existence" if object_type.startswith("agent_") else "dates"
        for source_key, transformed_key in [("notes", "notes"),
                                            ("rights_statements", "rights"),
                                            (date_source_key, "dates"),
                                            ("extents", "extents"),
                                            ("children", "children")]:
            source_len = len(source.get(source_key, []))
            transformed_len = len(transformed.get(transformed_key, []))
            self.assertEqual(source_len, transformed_len,
                             "Found {} {} in source but {} {} in transformed.".format(
                                 source_len, source_key, transformed_len, transformed_key))

    def check_agent_counts(self, source, transformed):
        """Checks for correct counts of agents and other creators."""
        source_creator_count = len([obj for obj in source.get("linked_agents", []) if obj.get("role") == "creator"])
        source_agent_count = len([obj for obj in source.get("linked_agents", []) if obj.get("role") != "creator"])
        self.assertTrue(
            source_creator_count == len(transformed.get("creators", [])),
            "Expecting {} creators, got {}".format(source_agent_count, len(transformed.get("creators", []))))
        self.assertEqual(
            source_agent_count, len(transformed.get("agents", [])),
            "Expecting {} agents, got {} instead".format(source_agent_count, len(transformed.get("agents", []))))
