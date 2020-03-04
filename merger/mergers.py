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

    def merge(self, object_type, object):
        """Main merge function. Merges transformed object into matched objects
           if they exist and then persists the merged object, or simply persists
           the transformed object if no matches are found."""
        try:
            identifier = self.get_identifier(object)
            target_object_type = self.get_target_object_type(object)
            additional_data = self.get_additional_data(object, target_object_type)
            merged = self.combine_data(object, additional_data) if additional_data else object
            send_post_request(
                settings.TRANSFORM_URL,
                {"object_type": target_object_type, "object": merged})
            return merged
        except Exception as e:
            raise MergeError("Error merging {}: {}".format(identifier, e))

    def get_identifier(self, object):
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

    def get_additional_data(self, object, object_type):
        base_fields = ["dates", "languages"]
        extended_fields = base_fields + ["extents"]
        data = {}
        fields = base_fields if object_type == "archival_object" else extended_fields
        for field in fields:
            if not object.get(field):
                value = self.aspace_helper.closest_parent_value(object.get("uri"), field)
                data[field] = value
        if object_type == "archival_object_collection":
            data["linked_agents"] = data.get("linked_agents", []) + self.aspace_helper.closest_creators(object.get("uri"))
            # TODO: get children
        return data

    def combine_data(self, object, additional_data):
        for k, v in additional_data.items():
            object[k] = v
        return object


class ArrangementMapMerger(BaseMerger):

    def get_target_object_type(self, data):
        return "resource"

    def get_additional_data(self, object, object_type):
        return self.aspace.client.get(object["archivespace_uri"])

    def combine_data(self, object, additional_data):
        """Prepend Cartographer ancestors to AS ancestors."""
        additional_data["ancestors"].insert(0, object["ancestors"])
        # TODO: Something with children??
        return additional_data


class AgentMerger(BaseMerger):
    pass


class ResourceMerger(BaseMerger):

    def get_additional_data(self, object, object_type):
        return None
        # TODO: return data from Cartographer
        # return self.cartographer_client.get("find-by-id", {"uri": object["uri"]}).json()

    def combine_data(self, object, additional_data):
        """Prepend Cartographer ancestors to AS ancestors."""
        object["ancestors"].insert(0, additional_data["ancestors"])
        # TODO: children?
        return object


class SubjectMerger(BaseMerger):
    pass
