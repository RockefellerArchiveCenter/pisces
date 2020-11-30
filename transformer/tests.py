import json
import os
import random

from django.test import TestCase
from django.urls import reverse
from fetcher.helpers import identifier_from_uri
from rest_framework.test import APIRequestFactory

from .models import DataObject
from .resources.configs import NOTE_TYPE_CHOICES_TRANSFORM
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
                    transformed = Transformer().run(object_type, source)
                    self.assertNotEqual(
                        transformed, False,
                        "Transformer returned an error: {}".format(transformed))
                    self.check_list_counts(source, transformed, object_type)
                    self.check_agent_counts(source, transformed)
                    self.check_references(transformed)
                    self.check_uri(transformed)
                    self.check_group(source, transformed)
                    self.check_parent(transformed)
                    self.check_formats(transformed)
                    self.check_component_id(source, transformed)
                    self.check_position(transformed, object_type)

    def check_list_counts(self, source, transformed, object_type):
        """Checks that lists of items are the same on source and data objects.

        Since transformer logic inherits dates from parent objects in some
        circumstances, the test for these is less stringent and allows for
        dates on transformed objects that do not exist on source objects.
        """
        date_source_key = "dates_of_existence" if object_type.startswith("agent_") else "dates"
        for source_key, transformed_key in [("notes", "notes"),
                                            (date_source_key, "dates"),
                                            ("extents", "extents"),
                                            ("children", "children")]:
            source_len = len(
                [n for n in source.get(source_key, []) if (n["publish"] and n["jsonmodel_type"] in NOTE_TYPE_CHOICES_TRANSFORM)]
            ) if source_key == "notes" else len(source.get(source_key, []))
            transformed_len = len(transformed.get(transformed_key, []))
            self.assertEqual(source_len, transformed_len,
                             "Found {} {} in source but {} {} in transformed.".format(
                                 source_len, source_key, transformed_len, transformed_key))

    def check_agent_counts(self, source, transformed):
        """Checks for correct counts of agents and other creators."""
        source_creator_count = len([obj for obj in source.get("linked_agents", []) if obj.get("role") == "creator"])
        source_person_count = len([obj for obj in source.get("linked_agents", []) if obj.get("type") == "agent_person"])
        source_organization_count = len([obj for obj in source.get("linked_agents", []) if obj.get("type") == "agent_corporate_entity"])
        source_family_count = len([obj for obj in source.get("linked_agents", []) if obj.get("type") == "agent_family"])
        if source["jsonmodel_type"] in ["archival_object", "resource", "subject"]:
            self.assertTrue(
                source_creator_count == len(transformed.get("creators", [])),
                "Expecting {} creators, got {}".format(
                    source_creator_count, len(transformed.get("creators", []))))
            self.assertEqual(
                source_person_count, len(transformed.get("people", [])),
                "Expecting {} people, got {} instead".format(
                    source_person_count, len(transformed.get("people", []))))
            self.assertEqual(
                source_organization_count, len(transformed.get("organizations", [])),
                "Expecting {} organizations, got {} instead".format(
                    source_organization_count, len(transformed.get("organizations", []))))
            self.assertEqual(
                source_family_count, len(transformed.get("families", [])),
                "Expecting {} families, got {} instead".format(
                    source_family_count, len(transformed.get("families", []))))
        else:
            key_map = {
                "agent_corporate_entity": "organizations",
                "agent_person": "people",
                "agent_family": "families"
            }
            key = key_map[source["jsonmodel_type"]]
            self.assertEqual(
                len(transformed.get(key)), 1,
                "Expecting a reference to self in {}".format(key))

    def check_references(self, transformed):
        for key in ["people", "organizations", "families", "terms", "creators", "ancestors", "children"]:
            for obj in transformed.get(key, []):
                for prop in ["identifier", "title", "type"]:
                    self.assertIsNot(
                        obj.get(prop), None,
                        "{} missing from {} reference in {}".format(prop, key, transformed["uri"]))

    def check_uri(self, transformed):
        _, path, identifier = transformed["uri"].split("/")
        self.assertEqual(path, "{}s".format(transformed["type"]))
        self.assertEqual(identifier, identifier_from_uri(transformed["external_identifiers"][0]["identifier"]))
        self.assertTrue(DataObject.objects.filter(es_id=identifier).exists())

    def check_parent(self, transformed):
        if transformed.get("ancestors"):
            self.assertEqual(transformed.get("parent"), transformed["ancestors"][0]["identifier"])

    def check_group(self, source, transformed):
        group = transformed.get("group")
        if len(source.get("ancestors", [])):
            self.assertEqual(group["identifier"], "/collections/{}".format(identifier_from_uri(source["ancestors"][-1]["ref"])))
        else:
            self.assertEqual(group["identifier"], transformed.get("uri"))

    def check_formats(self, transformed):
        """Cary Reich papers have `Sound recordings` as a subject term at the top
        level, so all objects from this collection should include `audio` in the
        formats list.
        """
        if transformed["group"]["identifier"] == "/collections/gfvm2HihpLwCTnKgpDtdhR":
            self.assertIn("audio", transformed.get("formats"))

    def check_component_id(self, source, transformed):
        if source.get("component_id"):
            self.assertEqual(transformed["title"], "{}, {} {}".format(source["title"], source["level"].capitalize(), source["component_id"]))

    def check_position(self, transformed, object_type):
        if object_type in ["archival_object", "resource"]:
            self.assertTrue(isinstance(transformed["position"], int))

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
