import json

from jsonschema.exceptions import ValidationError
from odin.codecs import json_codec
from rac_schemas import is_valid

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

    Selects the appropriate mapping configs, transforms and validates data.
    Validated data is saved to the application's database as a DataObject.

    Args:
        object_type (str): the object type of the source data.
        data (dict): the source data to be transformed.
    """

    def run(self, object_type, data):
        try:
            self.identifier = data.get("uri")
            from_resource, mapping, schema = self.get_mapping_classes(object_type)
            transformed = self.get_transformed_object(data, from_resource, mapping)
            is_valid(transformed, schema)
            self.save_validated(transformed)
            return transformed
        except ValidationError as e:
            raise TransformError("Transformed data is invalid: {}".format(e))
        except Exception as e:
            raise TransformError("Error transforming {} {}: {}".format(object_type, self.identifier, str(e)))

    def get_mapping_classes(self, object_type):
        TYPE_MAP = {
            "agent_person": (SourceAgentPerson, SourceAgentPersonToAgent, "agent.json"),
            "agent_corporate_entity": (SourceAgentCorporateEntity, SourceAgentCorporateEntityToAgent, "agent.json"),
            "agent_family": (SourceAgentFamily, SourceAgentFamilyToAgent, "agent.json"),
            "resource": (SourceResource, SourceResourceToCollection, "collection.json"),
            "archival_object": (SourceArchivalObject, SourceArchivalObjectToObject, "object.json"),
            "archival_object_collection": (SourceArchivalObject, SourceArchivalObjectToCollection, "collection.json"),
            "subject": (SourceSubject, SourceSubjectToTerm, "term.json")
        }
        return TYPE_MAP[object_type]

    def get_transformed_object(self, data, from_resource, mapping):
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        return self.remove_keys_from_dict(transformed)

    def remove_keys_from_dict(self, data, target_key="$"):
        """Removes all matching keys from dict."""
        modified_dict = {}
        if hasattr(data, 'items'):
            for key, value in data.items():
                if key != target_key:
                    if isinstance(value, dict):
                        modified_dict[key] = self.remove_keys_from_dict(data[key])
                    elif isinstance(value, list):
                        modified_dict[key] = [self.remove_keys_from_dict(i) for i in data[key]]
                    else:
                        modified_dict[key] = value
        else:
            return data
        return modified_dict

    def save_validated(self, data):
        es_id = data["uri"].split("/")[-1]
        try:
            existing = DataObject.objects.get(es_id=es_id)
            existing.data = data
            existing.indexed = False
            existing.save()
        except DataObject.DoesNotExist:
            DataObject.objects.create(
                es_id=es_id,
                object_type=data["type"],
                data=data,
                indexed=False)
