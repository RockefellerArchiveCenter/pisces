import re

from .helpers import (ArchivesSpaceHelper, closest_creators,
                      closest_parent_value, combine_references)


class MergeError(Exception):
    pass


class BaseMerger:
    """Base merger class."""

    def __init__(self, clients):
        try:
            self.aspace_helper = ArchivesSpaceHelper(clients["aspace"])
            self.cartographer_client = clients["cartographer"]
        except Exception as e:
            raise MergeError(e)

    def merge(self, object_type, object):
        """Main merge function.

        Fetches and merges additional data from secondary data sources, then
        delivers merged data to the configured URL."""
        try:
            identifier = self.get_identifier(object)
            target_object_type = self.get_target_object_type(object)
            additional_data = self.get_additional_data(object, target_object_type)
            return self.combine_data(object, additional_data) if additional_data else object, target_object_type
        except Exception as e:
            print(e)
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

    def get_target_object_type(self, data):
        """Returns object type.

        Archival objects that have children are mapped differently from those
        without.
        """
        if data.get("jsonmodel_type") == "archival_object":
            if self.aspace_helper.has_children(data["uri"]):
                return "archival_object_collection"
        return data.get("jsonmodel_type")


class ArchivalObjectMerger(BaseMerger):

    def get_additional_data(self, object, object_type):
        """Fetches additional data from ArchivesSpace and Cartographer.

        Args:
            object (dict): source object (an ArchivesSpace archival object record).
            object_type (str): the source object type, either `archival_object`
                or `archival_object_collection`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {"ancestors": [], "children": [], "linked_agents": []}
        data.update(self.get_cartographer_data(object))
        data.update(self.get_archivesspace_data(object, object_type))
        return data

    def get_cartographer_data(self, object):
        """Gets ancestors, if any, from the archival object's resource record in
        Cartographer."""
        data = {"ancestors": []}
        resp = self.cartographer_client.get(
            "/api/find-by-uri/", params={"uri": object["resource"]["ref"]})
        if resp.status_code == 200:
            json = resp.json()
            if json["count"] >= 1:
                for a in json["results"][0].get("ancestors"):
                    data["ancestors"].append(a)
        return data

    def get_archival_object_collection_data(self, object):
        """Gets additional data for archival_object_collections."""
        data = {"children": []}
        data["linked_agents"] = data.get(
            "linked_agents", []) + closest_creators(object)
        data["children"] = self.aspace_helper.get_archival_object_children(
            object["resource"]["ref"], object["uri"])
        return data

    def get_language_data(self, object, data):
        """Gets language data from ArchivesSpace.

        This logic accomodates ArchivesSpace API changes between 2.6 and 2.7.
        """
        if "lang_materials" in object:
            if object.get("lang_materials") in ["", [], {}]:
                data["lang_materials"] = closest_parent_value(object, "lang_materials")
        else:
            data["language"] = closest_parent_value(object, "language")
        return data

    def parse_instances(self, object, data):
        extents = []
        parseable = [i for i in object["instances"] if
                     all(i_type in i.get("sub_container", {})
                         for i_type in ["indicator_2", "type_2"])]
        for instance in parseable:
            extent = {}
            try:
                range = sorted([int(re.sub("[^0-9]", "", i.strip()))
                                for i in instance["sub_container"]["indicator_2"].split("-")])
                extent["extent_type"] = instance["sub_container"]["type_2"]
                extent["number"] = range[-1] - range[0] if len(range) > 1 else 1
                extents.append(extent)
            except ValueError:
                pass
        return extents

    def get_archivesspace_data(self, object, object_type):
        """Gets dates, languages, extent and children from archival object's
        resource record in ArchivesSpace.
        """
        data = {"linked_agents": [], "children": []}
        if object.get("dates") in ["", [], {}, None]:
            data["dates"] = closest_parent_value(object, "dates")
        data.update(self.get_language_data(object, data))
        extent_data = object.get("extents") if object.get("extents") else self.parse_instances(object, data)
        if not extent_data and object_type == "archival_object_collection":
            extent_data = closest_parent_value(object, "extents")
        data["extents"] = extent_data
        if object_type == "archival_object_collection":
            data.update(self.get_archival_object_collection_data(object))
        return data

    def combine_data(self, object, additional_data):
        """Combines additional data with source data.

        Moves data from resolved objects to expected keys within main object.
        """
        for k, v in additional_data.items():
            if isinstance(v, list):
                object[k] = object.get(k, []) + v
            else:
                object[k] = v
        return combine_references(object)


class ArrangementMapMerger(BaseMerger):

    def get_target_object_type(self, data):
        return "resource"

    def get_additional_data(self, object, object_type):
        """Fetches the ArchivesSpace resource record referenced by the
        ArrangementMapComponent.

        Args:
            object (dict): source object (an ArrangementMapComponent).
            object_type (str): the source object type, `arrangement_map_component`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {"children": [], "ancestors": []}
        data.update(
            self.aspace_helper.aspace.client.get(
                object["archivesspace_uri"],
                params={"resolve": ["subjects", "linked_agents"]}).json())
        if not object.get("children"):
            data["children"] = self.aspace_helper.get_resource_children(object["archivesspace_uri"])
        return data

    def combine_data(self, object, additional_data):
        """Adds Cartographer ancestors to ArchivesSpace resource record."""
        ancestors = []
        for a in object.get("ancestors"):
            a["type"] = "collection"
            ancestors.append(a)
        additional_data["ancestors"] = ancestors
        return combine_references(additional_data)


class AgentMerger(BaseMerger):
    pass


class ResourceMerger(BaseMerger):

    def get_additional_data(self, object, object_type):
        """Gets additional data from Cartographer and ArchivesSpace.

        Args:
            object (dict): source object (an ArchivesSpace resource record).
            object_type (str): the source object type, always `resource`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {"children": [], "ancestors": []}
        data.update(self.get_cartographer_data(object))
        data.update(self.get_archivesspace_data(object))
        return data

    def get_cartographer_data(self, object):
        """Returns ancestors (if any) for the resource record from
        Cartographer."""
        data = {"ancestors": []}
        resp = self.cartographer_client.get(
            "/api/find-by-uri/", params={"uri": object["uri"]})
        if resp.status_code == 200:
            json = resp.json()
            if json["count"] > 0:
                data["ancestors"] = json["results"][0].get("ancestors", [])
        return data

    def get_archivesspace_data(self, object):
        """Returns the first level of the resource record tree from
        ArchivesSpace."""
        data = {"children": []}
        data["children"] = self.aspace_helper.get_resource_children(object["uri"])
        return data

    def combine_data(self, object, additional_data):
        """Combines existing ArchivesSpace data with Cartographer data.

        Adds Cartographer ancestors to object's `ancestors` key, and
        ArchivesSpace children to object's `children` key.
        """
        object["ancestors"] = additional_data["ancestors"]
        object["children"] = additional_data["children"]
        return combine_references(object)


class SubjectMerger(BaseMerger):
    pass
