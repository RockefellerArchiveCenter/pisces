import json

from fetcher.helpers import instantiate_electronbond, send_post_request
from pisces import settings
from silk.profiling.profiler import silk_profile

from .helpers import ArchivesSpaceHelper


class MergeError(Exception):
    pass


class BaseMerger:
    """Base merger class."""

    def __init__(self):
        try:
            self.aspace_helper = ArchivesSpaceHelper()
            self.cartographer_client = instantiate_electronbond(settings.CARTOGRAPHER)
        except Exception as e:
            raise MergeError(e)

    @silk_profile()
    def merge(self, object_type, object):
        """Main merge function.

        Fetches and merges additional data from secondary data sources, then
        delivers merged data to the configured URL."""
        try:
            identifier = self.get_identifier(object)
            target_object_type = self.get_target_object_type(object)
            additional_data = self.get_additional_data(object, target_object_type)
            merged = self.combine_data(object, additional_data) if additional_data else object
            send_post_request(
                settings.TRANSFORM_URL,
                {"object_type": target_object_type, "object": merged})
            return json.dumps(merged)
        except Exception as e:
            raise MergeError("Error merging {}: {}".format(identifier, e))

    def get_identifier(self, object):
        """Returns the identifier for the object."""
        try:
            identifier = object["uri"]
        except KeyError:
            identifier = object["ref"]
        return identifier

    def get_additional_data(self, object, object_type):
        return None

    @silk_profile()
    def get_target_object_type(self, data):
        """Returns object type.

        Archival objects that have children are mapped differently from those
        without.
        """
        if data.get("jsonmodel_type") == "archival_object":
            if ArchivesSpaceHelper().has_children(data['uri']):
                return "archival_object_collection"
        return data.get("jsonmodel_type")


class ArchivalObjectMerger(BaseMerger):

    @silk_profile()
    def get_additional_data(self, object, object_type):
        """Fetches additional data from ArchivesSpace."""
        base_fields = ["dates", "language"]
        extended_fields = base_fields + ["extents"]
        data = {}
        fields = base_fields if object_type == "archival_object" else extended_fields
        for field in fields:
            if object.get(field) in ['', [], {}, None]:
                value = self.aspace_helper.closest_parent_value(object.get("uri"), field)
                data[field] = value
        if object_type == "archival_object_collection":
            data["linked_agents"] = data.get("linked_agents", []) + self.aspace_helper.closest_creators(object.get("uri"))
            # TODO: get children
        return data

    @silk_profile()
    def combine_data(self, object, additional_data):
        for k, v in additional_data.items():
            object[k] = v
        return object


class ArrangementMapMerger(BaseMerger):

    def get_target_object_type(self, data):
        return "resource"

    @silk_profile()
    def get_additional_data(self, object, object_type):
        """Fetches the ArchivesSpace resource record referenced by the MapComponent."""
        return self.aspace_helper.aspace.client.get(object["archivesspace_uri"]).json()

    @silk_profile()
    def combine_data(self, object, additional_data):
        """Prepends Cartographer ancestors to ArchivesSpace ancestors."""
        additional_data["ancestors"] = object["ancestors"]
        # TODO: Something with children??
        return additional_data


class AgentMerger(BaseMerger):
    pass


class ResourceMerger(BaseMerger):

    @silk_profile()
    def get_additional_data(self, object, object_type):
        """Gets additional data from Cartographer, or returns None if no
        matching component is found."""
        resp = self.cartographer_client.get("/api/find-by-uri/", params={"uri": object["uri"]}).json()
        if resp["count"] == 0:
            return None
        else:
            return resp["results"][0]

    @silk_profile()
    def combine_data(self, object, additional_data):
        """Prepends Cartographer ancestors to ArchivesSpace ancestors."""
        object["ancestors"] = additional_data.get("ancestors", [])
        # TODO: children?
        return object


class SubjectMerger(BaseMerger):
    pass
