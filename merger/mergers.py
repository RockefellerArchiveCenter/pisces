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
        """Fetches additional data from ArchivesSpace and Cartographer.

        Args:
            object (dict): source object (an ArchivesSpace archival object record).
            object_type (str): the source object type, either `archival_object`
                or `archival_object_collection`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {}
        data.update(self.get_cartographer_data(object))
        data.update(self.get_archivesspace_data(object, object_type))
        return data

    def get_cartographer_data(self, object):
        """Gets ancestors, if any, from the archival object's resource record in
        Cartographer."""
        data = {}
        resp = self.cartographer_client.get("/api/find-by-uri/", params={"uri": object["resource"]["ref"]}).json()
        if resp["count"] >= 1:
            data["ancestors"] = resp["results"][0].get("ancestors")
        return data

    def get_archivesspace_data(self, object, object_type):
        """Gets dates, languages and extent data from archival object's resource
        record in ArchivesSpace."""
        data = {}
        base_fields = ["dates", "language"]
        fields = base_fields if object_type == "archival_object" else base_fields + ["extents"]
        for field in fields:
            if object.get(field) in ['', [], {}, None]:
                value = self.aspace_helper.closest_parent_value(object.get("uri"), field)
                data[field] = value
        if object_type == "archival_object_collection":
            data["linked_agents"] = data.get("linked_agents", []) + self.aspace_helper.closest_creators(object.get("uri"))
        return data

    @silk_profile()
    def combine_data(self, object, additional_data):
        for k, v in additional_data.items():
            if isinstance(v, list):
                object[k] = object.get(k, []) + v
            else:
                object[k] = v
        return object


class ArrangementMapMerger(BaseMerger):

    def get_target_object_type(self, data):
        return "resource"

    @silk_profile()
    def get_additional_data(self, object, object_type):
        """Fetches the ArchivesSpace resource record referenced by the
        ArrangementMapComponent.

        Args:
            object (dict): source object (an ArrangementMapComponent).
            object_type (str): the source object type, `arrangement_map_component`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        return self.aspace_helper.aspace.client.get(object["archivesspace_uri"]).json()

    @silk_profile()
    def combine_data(self, object, additional_data):
        """Adds Cartographer ancestors to ArchivesSpace resource record."""
        additional_data["ancestors"] = object.get("ancestors", [])
        return additional_data


class AgentMerger(BaseMerger):
    pass


class ResourceMerger(BaseMerger):

    @silk_profile()
    def get_additional_data(self, object, object_type):
        """Gets additional data from Cartographer and ArchivesSpace.

        Returns ancestors (if any) for the resource record from Cartographer,
        and returns the first level of the resource record tree from
        ArchivesSpace.

        Args:
            object (dict): source object (an ArchivesSpace resource record).
            object_type (str): the source object type, always `resource`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {"children": [], "ancestors": []}
        cartographer_data = self.cartographer_client.get("/api/find-by-uri/", params={"uri": object["uri"]}).json()
        if cartographer_data["count"] > 0:
            data["ancestors"] = cartographer_data["results"][0].get("ancestors", [])
        as_tree = self.aspace_helper.aspace.client.get("{}/tree".format(object["uri"].rstrip("/"))).json()
        for child in as_tree.get("children"):
            del child["children"]
            data["children"].append(child)
        return data

    @silk_profile()
    def combine_data(self, object, additional_data):
        """Combines existing ArchivesSpace data with Cartographer data.

        Adds Cartographer ancestors to object's `ancestors` key, and
        ArchivesSpace children to object's `children` key.
        """
        object["ancestors"] = additional_data["ancestors"]
        object["children"] = additional_data["children"]
        return object


class SubjectMerger(BaseMerger):
    pass
