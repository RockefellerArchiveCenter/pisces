import json
import os

import vcr
from django.test import TestCase
from django.urls import reverse
from pisces import settings
from rest_framework.test import APIRequestFactory

from .mergers import (AgentMerger, ArchivalObjectMerger, ArrangementMapMerger,
                      ResourceMerger, SubjectMerger)
from .views import MergeView

merger_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/merger',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)


object_types = [
    ("agent_corporate_entity", AgentMerger, ["agent_corporate_entity"]),
    ("agent_family", AgentMerger, ["agent_family"]),
    ("agent_person", AgentMerger, ["agent_person"]),
    ("archival_object", ArchivalObjectMerger, ["archival_object", "archival_object_collection"]),
    ("resource", ResourceMerger, ["resource"]),
    ("subject", SubjectMerger, ["subject"]),
    ("arrangement_map_component", ArrangementMapMerger, ["resource"])
]


class MergerTest(TestCase):
    """Tests Merger and MergerView."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_merge(self):
        """Tests Merge."""
        for source_object_type, merger, target_object_types in object_types:
            with merger_vcr.use_cassette("{}-merge.json".format(source_object_type)) as cass:
                for f in os.listdir(os.path.join("fixtures", "merger", source_object_type)):
                    with open(os.path.join("fixtures", "merger", source_object_type, f), "r") as json_file:
                        source = json.load(json_file)
                        merged = merger().merge(source_object_type, source)
                        self.assertNotEqual(
                            merged, False,
                            "Transformer returned an error: {}".format(merged))
                        transform_requests = len([r for r in cass.requests if r.uri == settings.TRANSFORM_URL])
                        self.assertTrue(
                            transform_requests, 1,
                            "Transform service should have been called once, was called {}".format(transform_requests))
                        merged_data = json.loads(merged)
                        self.assertTrue(merged_data.get("jsonmodel_type") in target_object_types)
                        self.check_counts(source, source_object_type, merged_data, merged_data.get("jsonmodel_type"))

    def check_counts(self, source, source_object_type, merged, target_object_type):
        """Tests counts of data keys in merged object.

        Archival objects are expected to have values in dates and languages fields.
        Archival object collections are expected to have values in dates,
            languages, extents, linked_agents and children fields
        Resources should have at least as many ancestors in the merged data as
            in the source.
        """
        if target_object_type == "archival_object":
            for field in ["dates", "language"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
        elif target_object_type == "archival_object_collection":
            for field in ["dates", "language", "extents", "linked_agents", "children"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
        elif target_object_type == "resource":
            if source_object_type == "arrangement_map":
                self.assertTrue(len(merged.get("ancestors", [])) > len(source.get("ancestors", [])),
                                "{} does not have more ancestors in merged data than source data.".format(merged))
            else:
                self.assertTrue(len(merged.get("ancestors", [])) >= len(source.get("ancestors", [])),
                                "{} does not have equal or more ancestors in merged data than source data.".format(merged))

    def not_empty(self, value):
        return False if value in ['', [], {}, None] else True

    def test_merge_views(self):
        """Tests MergeView."""
        for object_type, merger, _ in object_types:
            with merger_vcr.use_cassette("{}-merge.json".format(object_type)) as cass:
                for f in os.listdir(os.path.join("fixtures", "merger", object_type)):
                    with open(os.path.join("fixtures", "merger", object_type, f), "r") as json_file:
                        source = json.load(json_file)
                        request = self.factory.post(
                            reverse("merge"),
                            data={"object_type": object_type, "object": source},
                            format="json")
                        response = MergeView().as_view()(request)
                        self.assertEqual(response.status_code, 200, "Request error: {}".format(response.data))
                        transform_requests = len([r for r in cass.requests if r.uri == settings.TRANSFORM_URL])
                        self.assertTrue(
                            transform_requests, 1,
                            "Transform service should have been called once, was called {}".format(transform_requests))
