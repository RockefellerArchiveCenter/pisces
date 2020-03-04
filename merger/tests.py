import json
import os
from unittest import mock

import vcr
from django.test import TestCase
from django.urls import reverse
from pisces import settings
from rest_framework.test import APIRequestFactory

from .mergers import (AgentMerger, ArchivalObjectMerger, ResourceMerger,
                      SubjectMerger)
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
    ("archival_objects", ArchivalObjectMerger, ["archival_object", "archival_object_collection"]),
    ("resources", ResourceMerger, ["resource"]),
    ("subjects", SubjectMerger, ["subject"]),
    # TODO: add arrangement maps
    # ("arrangement_maps", ArrangementMapMerger, ["resource"])
]


class MergerTest(TestCase):
    """Tests Merger and MergerView."""

    def setUp(self):
        self.factory = APIRequestFactory()

    @mock.patch("fetcher.helpers.send_post_request")
    def test_merge(self, mock_post):
        """Tests Merge."""
        for source_object_type, merger, target_object_types in object_types:
            with merger_vcr.use_cassette("{}-merge.json".format(source_object_type)):
                for f in os.listdir(os.path.join("fixtures", "merger", source_object_type)):
                    with open(os.path.join("fixtures", "merger", source_object_type, f), "r") as json_file:
                        source = json.load(json_file)
                        merged = merger().merge(source_object_type, source)
                        self.assertNotEqual(
                            merged, False,
                            "Transformer returned an error: {}".format(merged))
                        # mock_post.assert_called_once_with(settings.TRANSFORM_URL)
                        # mock_post.reset_mock()
                        self.assertTrue(merged.get("jsonmodel_type") in target_object_types)
                        self.check_counts(source, source_object_type, merged.get("object"), merged.get("object_type"))

    def check_counts(self, source, source_object_type, merged, target_object_type):
        """Tests counts of data keys in merged object.

        Archival objects are expected to have values in dates and languages fields.
        Archival object collections are expected to have values in dates,
            languages, extents, linked_agents and children fields
        Resources should have as many ancestors in the merged data as in the
            source, if not more.
        """
        if target_object_type == "archival_object":
            for field in ["dates", "languages"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
        elif target_object_type == "archival_object_collection":
            for field in ["dates", "languages", "extents", "linked_agents", "children"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
        elif target_object_type == "resource":
            if source_object_type == "arrangement_map":
                self.assertTrue(len(merged.get("ancestors")) > len(source.get("ancestors")),
                                "{} does not have more ancestors in merged data than source data.".format(merged))
            else:
                self.assertTrue(len(merged.get("ancestors")) >= len(source.get("ancestors")),
                                "{} does not have equal or more ancestors in merged data than source data.".format(merged))

    def not_empty(self, value):
        return False if value in ['', [], {}, None] else True

    @mock.patch("fetcher.helpers.send_post_request")
    def test_merge_views(self, mock_post):
        """Tests MergeView."""
        for object_type, merger, _ in object_types:
            for f in os.listdir(os.path.join("fixtures", "merger", object_type)):
                with open(os.path.join("fixtures", "merger", object_type, f), "r") as json_file:
                    source = json.load(json_file)
                    request = self.factory.post(reverse('merge'), json=source)
                    response = MergeView().as_view()(request)
                    self.assertEqual(response.status_code, 200, "Request error: {}".format(response.data))
                    mock_post.assert_called_once_with(settings.TRANSFORM_URL)
                    mock_post.reset_mock()
