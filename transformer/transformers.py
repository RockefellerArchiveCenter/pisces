import json

from asterism.resources import archivesspace
from fetcher.helpers import send_post_request
from odin.codecs import json_codec
from pisces import settings
from requests.exceptions import ConnectionError

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

    Exposes a `get_identifier` method, which returns an identifier for the
    object being processed, as well as a `get_transformed_object()` method,
    which is expected to return a dict representation of the transformed object.
    """

    def run(self, data):
        try:
            self.identifier = self.get_identifier(data)
            self.object_type = self.get_object_type(data)
            transformed = self.get_transformed_object(data)
            return json.dumps(transformed)
        except ConnectionError:
            raise TransformError("Could not connect to {}".format(settings.DELIVERY_URL))
        except Exception as e:
            raise TransformError("Error transforming {} {}: {}".format(self.object_type, self.identifier, str(e)))


class CartographerDataTransformer(BaseTransformer):
    """Transforms Cartographer data.

    Iterates through its children and transforms each into a Collection.
    Transformed data is delivered to a configured DELIVERY_URL.
    """

    def get_identifier(self, data):
        return data.get("ref")

    def get_object_type(self, data):
        return "arrangement_map"

    def get_transformed_object(self, data):
        self.transformed_list = []
        for child in data.get("children"):
            self.identifier = self.get_identifier(child)
            self.process_child(child)
        return self.transformed_list

    def process_child(self, data):
        from_obj = json_codec.loads(json.dumps(data), resource=CartographerMapComponent)
        transformed = json.loads(json_codec.dumps(CartographerMapComponentToCollection.apply(from_obj)))
        send_post_request(settings.DELIVERY_URL, transformed)
        self.transformed_list.append(transformed)
        for child in data.get("children", []):
            self.identifier = self.get_identifier(child)
            self.process_child(child)


class ArchivesSpaceDataTransformer(BaseTransformer):
    """Transforms ArchivesSpace data.

    Uses a three-tuple to set mapping rules based on the source data's object
    type.
    """

    def get_identifier(self, data):
        return data.get("uri")

    def get_transformed_object(self, data):
        self.object_type = self.get_object_type(data)
        TYPE_MAP = (
            ("agent_person", archivesspace.ArchivesSpaceAgentPerson, ArchivesSpaceAgentPersonToAgent),
            ("agent_corporate_entity", archivesspace.ArchivesSpaceAgentCorporateEntity, ArchivesSpaceAgentCorporateEntityToAgent),
            ("agent_family", archivesspace.ArchivesSpaceAgentFamily, ArchivesSpaceAgentFamilyToAgent),
            ("resource", archivesspace.ArchivesSpaceResource, ArchivesSpaceResourceToCollection),
            ("archival_object", archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToObject),
            ("archival_object_collection", archivesspace.ArchivesSpaceArchivalObject, ArchivesSpaceArchivalObjectToCollection),
            ("subject", archivesspace.ArchivesSpaceSubject, ArchivesSpaceSubjectToTerm))
        from_type, from_resource, mapping = [t for t in TYPE_MAP if t[0] == self.object_type][0]
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        send_post_request(settings.DELIVERY_URL, transformed)
        return transformed

    def get_object_type(self, data):
        """Parses out archival_objects with children from those without.

        Archival objects that have children are mapped differently from those
        without.
        """
        if data.get("jsonmodel_type") == "archival_object":
            if ArchivesSpaceHelper().has_children(data['uri']):
                return "archival_object_collection"
        return data.get("jsonmodel_type")
