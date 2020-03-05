import json

from odin.codecs import json_codec
from pisces import settings
from requests.exceptions import ConnectionError
from silk.profiling.profiler import silk_profile

from .mappings import (SourceAgentCorporateEntityToAgent,
                       SourceAgentFamilyToAgent, SourceAgentPersonToAgent,
                       SourceArchivalObjectToCollection,
                       SourceArchivalObjectToObject,
                       SourceResourceToCollection, SourceSubjectToTerm)
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

    @silk_profile()
    def run(self, object_type, data):
        try:
            self.identifier = data.get("uri")
            mapping_configs = self.get_mapping_configs(object_type)
            transformed = self.get_transformed_object(data, *mapping_configs)
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
        # validate
        # persist
        return transformed
