import json

from asterism.resources import archivesspace
from fetcher.helpers import send_post_request
from odin.codecs import json_codec
from pisces import settings
from requests.exceptions import ConnectionError
from silk.profiling.profiler import silk_profile

from .mappings import (ArchivesSpaceAgentCorporateEntityToAgent,
                       ArchivesSpaceAgentFamilyToAgent,
                       ArchivesSpaceAgentPersonToAgent,
                       ArchivesSpaceArchivalObjectToCollection,
                       ArchivesSpaceArchivalObjectToObject,
                       ArchivesSpaceResourceToCollection,
                       ArchivesSpaceSubjectToTerm,
                       CartographerMapComponentToCollection)
from .mappings_helpers import ArchivesSpaceHelper
from .resources import CartographerMapComponent


class TransformError(Exception):
    """Sets up the error messaging for AS transformations."""
    pass


class BaseTransformer:
    """Base Data Transformer.

    Exposes the following methods:
        `get_identifier`: returns an identifier for the object being processed.
        `get_object_type`: returns the type of object being processed.
        `get_mapping_configs`: returns a two-tuple of the type to map from, and
            the mapping to be applied to the object.
        `get_transformed_object`: returns a dict representation of the
            transformed object.
    """

    @silk_profile()
    def run(self, data):
        try:
            self.identifier = self.get_identifier(data)
            object_type = self.get_object_type(data)
            mapping_configs = self.get_mapping_configs(object_type)
            transformed = self.get_transformed_object(data, *mapping_configs)
            return json.dumps(transformed)
        except ConnectionError:
            raise TransformError("Could not connect to {}".format(settings.DELIVERY_URL))
        except Exception as e:
            raise TransformError("Error transforming {} {}: {}".format(object_type, self.identifier, str(e)))


class CartographerDataTransformer(BaseTransformer):
    """Transforms Cartographer data."""

    def get_identifier(self, data):
        return data.get("ref")

    def get_object_type(self, data):
        return "arrangement_map"

    def get_mapping_configs(self, object_type):
        CARTOGRAPHER_TYPE_MAP = {
            "arrangement_map": (CartographerMapComponent, CartographerMapComponentToCollection)
        }
        return CARTOGRAPHER_TYPE_MAP[object_type]

    @silk_profile()
    def get_transformed_object(self, data, from_resource, mapping):
        self.transformed_list = []
        for child in data.get("children"):
            self.process_child(child, from_resource, mapping)
        return self.transformed_list

    @silk_profile()
    def process_child(self, data, from_resource, mapping):
        self.identifier = self.get_identifier(data)
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        send_post_request(settings.DELIVERY_URL, transformed)
        self.transformed_list.append(transformed)
        for child in data.get("children", []):
            self.process_child(child, from_resource, mapping)


class ArchivesSpaceDataTransformer(BaseTransformer):
    """Transforms ArchivesSpace data."""

    def get_identifier(self, data):
        return data.get("uri")

    def get_mapping_configs(self, object_type):
        ARCHIVESSPACE_TYPE_MAP = {
            "agent_person": (archivesspace.ArchivesSpaceAgentPerson, ArchivesSpaceAgentPersonToAgent),
            "agent_corporate_entity": (archivesspace.ArchivesSpaceAgentCorporateEntity, ArchivesSpaceAgentCorporateEntityToAgent),
            "agent_family": (archivesspace.ArchivesSpaceAgentFamily, ArchivesSpaceAgentFamilyToAgent),
            "resource": (archivesspace.ArchivesSpaceResource, ArchivesSpaceResourceToCollection),
            "archival_object": (archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToObject),
            "archival_object_collection": (archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToCollection),
            "subject": (archivesspace.ArchivesSpaceSubject, ArchivesSpaceSubjectToTerm)
        }
        return ARCHIVESSPACE_TYPE_MAP[object_type]

    @silk_profile()
    def get_transformed_object(self, data, from_resource, mapping):
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        send_post_request(settings.DELIVERY_URL, transformed)
        return transformed

    @silk_profile()
    def get_object_type(self, data):
        """Parses out archival_objects with children from those without.

        Archival objects that have children are mapped differently from those
        without.
        """
        if data.get("jsonmodel_type") == "archival_object":
            if ArchivesSpaceHelper().has_children(data['uri']):
                return "archival_object_collection"
        return data.get("jsonmodel_type")
