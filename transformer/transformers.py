import json
from os.path import join

import shortuuid
from jsonschema import validate
from odin.codecs import json_codec
from pisces import settings
from requests.exceptions import ConnectionError
from silk.profiling.profiler import silk_profile

from .mappings import (SourceAgentCorporateEntityToAgent,
                       SourceAgentFamilyToAgent, SourceAgentPersonToAgent,
                       SourceArchivalObjectToCollection,
                       SourceArchivalObjectToObject,
                       SourceResourceToCollection, SourceSubjectToTerm)
from .models import DataObject
from .resources.source import (SourceAgentCorporateEntity, SourceAgentFamily,
                               SourceAgentPerson, SourceArchivalObject,
                               SourceResource, SourceSubject)


class TransformError(Exception):
    """Sets up the error messaging for AS transformations."""
    pass


class Transformer:
    """Data Transformer.

    Exposes the following methods:
        `get_identifier`: returns an identifier for the object being processed.
        `get_object_type`: returns the type of object being processed.
        `get_mapping_configs`: returns a two-tuple of the type to map from, and
            the mapping to be applied to the object.
        `get_transformed_object`: returns a dict representation of the
            transformed object.
    """

    def __init__(self):
        with open(join(settings.BASE_DIR, "rac-data-model", "schema.json")) as sf:
            self.schema = json.load(sf)

    @silk_profile()
    def run(self, object_type, data):
        try:
            self.identifier = data.get("uri")
            mapping_configs = self.get_mapping_configs(object_type)
            transformed = self.get_transformed_object(data, *mapping_configs)
            self.validate_transformed(transformed)
            self.save_validated(transformed)
            return json.dumps(transformed)
        except ConnectionError:
            raise TransformError("Could not connect to {}".format(settings.MERGE_URL))
        except Exception as e:
            raise TransformError("Error transforming {} {}: {}".format(object_type, self.identifier, str(e)))

    def get_mapping_configs(self, object_type):
        TYPE_MAP = {
            "agent_person": (SourceAgentPerson, SourceAgentPersonToAgent),
            "agent_corporate_entity": (SourceAgentCorporateEntity, SourceAgentCorporateEntityToAgent),
            "agent_family": (SourceAgentFamily, SourceAgentFamilyToAgent),
            "resource": (SourceResource, SourceResourceToCollection),
            "archival_object": (SourceArchivalObject, SourceArchivalObjectToObject),
            "archival_object_collection": (SourceArchivalObject, SourceArchivalObjectToCollection),
            "subject": (SourceSubject, SourceSubjectToTerm)
        }
        return TYPE_MAP[object_type]

    @silk_profile()
    def get_transformed_object(self, data, from_resource, mapping):
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        return transformed

    @silk_profile()
    def validate_transformed(self, data):
        # TODO: return meaningful validation messages!
        validate(instance=data, schema=self.schema)

    @silk_profile()
    def save_validated(self, data):
        initial_queryset = DataObject.objects.filter(object_type=data["type"])
        for ident in data["external_identifiers"]:
            matches = DataObject.find_matches(
                ident["source"], ident["identifier"],
                initial_queryset=initial_queryset)
            if len(matches) > 1:
                raise Exception(
                    "Too many matches were found for {}".format(ident["identifier"]))
            elif len(matches) == 1:
                existing = matches[0]
                existing.data = data
                existing.indexed = False
                existing.save()
            else:
                DataObject.objects.create(
                    es_id=self.generate_identifier(),
                    object_type=data["type"],
                    data=data,
                    indexed=False)

    @silk_profile()
    def generate_identifier(self):
        shortuuid.set_alphabet('23456789abcdefghijkmnopqrstuvwxyz')
        return shortuuid.uuid()
