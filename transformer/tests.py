import asyncio
import json
import os
import random

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from .models import DataObject
from .transformers import Transformer
from .views import DataObjectUpdateByIdView, DataObjectViewSet

object_types = ["agent_corporate_entity", "agent_family", "agent_person",
                "archival_object", "resource", "subject",
                "archival_object_collection"]


class TransformerTest(TestCase):
    """Tests the transformations and mappings.

    Runs the transformations against fixtures of each object type. Additional
    checks are performed for object counts to ensure successful transformation.
    """

    def mappings(self):
        """Tests transformation of source data resources."""
        for object_type in object_types:
            for f in os.listdir(os.path.join("fixtures", "transformer", object_type)):
                with open(os.path.join("fixtures", "transformer", object_type, f), "r") as json_file:
                    source = json.load(json_file)
                    loop = asyncio.get_event_loop()
                    transformed = loop.run_until_complete(Transformer().run(object_type, source))
                    self.assertNotEqual(
                        transformed, False,
                        "Transformer returned an error: {}".format(transformed))
                    self.check_list_counts(source, transformed, object_type)
                    self.check_agent_counts(source, transformed)
                    self.check_uris(transformed)

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
            "Expecting {} creators, got {}".format(
                source_agent_count, len(transformed.get("creators", []))))
        self.assertEqual(
            source_agent_count, len(transformed.get("agents", [])),
            "Expecting {} agents, got {} instead".format(
                source_agent_count, len(transformed.get("agents", []))))

    def check_uris(self, transformed):
        for key in ["agents", "terms", "creators", "ancestors", "children"]:
            for obj in transformed.get(key, []):
                self.assertIsNot(
                    obj.get("uri"), None,
                    "URI missing from {} reference in {} {}".format(key, transformed["type"], transformed["es_id"]))

    def views(self):
        for object_type in ["agent", "collection", "object", "term"]:
            obj = random.choice(DataObject.objects.filter(object_type=object_type))
            obj.indexed = True
            obj.save()

        client = APIRequestFactory()
        for action in ["agents", "collections", "objects", "terms"]:
            view = DataObjectViewSet.as_view({"get": action})
            for clean in ["true", "false"]:
                request = client.get("{}?clean={}".format(reverse("dataobject-list"), clean))
                response = view(request)
                self.assertEqual(
                    response.status_code, 200,
                    "View error:  {}".format(response.data))
                if clean == "true":
                    self.assertEqual(
                        response.data["count"],
                        len(DataObject.objects.filter(object_type=action.rstrip("s"))))
                else:
                    self.assertEqual(
                        response.data["count"] + 1,
                        len(DataObject.objects.filter(object_type=action.rstrip("s"))))
                for obj in response.data["results"]:
                    self.assertTrue(
                        "$" not in obj,
                        "Odin mapping keys were not removed from data.")

        for object_type in ["agent", "collection", "object", "term"]:
            for action in ["deleted", "indexed"]:
                obj = random.choice(DataObject.objects.filter(object_type=object_type))
                obj_len = len(DataObject.objects.filter(object_type=object_type))
                request = client.post(
                    reverse("index-action-complete"),
                    data={"identifiers": [obj.es_id], "action": action},
                    format="json")
                response = DataObjectUpdateByIdView.as_view()(request)
                self.assertEqual(
                    response.status_code, 200,
                    "Update by ID error: {}".format(response.data))
                final_count = obj_len if action == "indexed" else obj_len - 1
                self.assertEqual(
                    len(DataObject.objects.filter(object_type=object_type)),
                    final_count, "{} {} objects were expected but {} found".format(
                        final_count, object_type, len(DataObject.objects.filter(object_type=object_type))))

    def test_transformer(self):
        self.mappings()
        self.views()
