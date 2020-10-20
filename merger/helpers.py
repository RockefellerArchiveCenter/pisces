from fetcher.helpers import instantiate_aspace
from pisces import settings


def get_ancestors(obj):
    """Returns the full resolved record for each ancestor."""
    for a in obj["ancestors"]:
        yield a["_resolved"]


def closest_parent_value(obj, key):
    """Iterates upwards through a hierarchy and returns the first match for a key.

    Iterates up through an archival object's ancestors and returns the first
    value which matches a given key."""
    for ancestor in get_ancestors(obj):
        if ancestor.get(key) not in ['', [], {}, None]:
            return ancestor[key]


def closest_creators(obj):
    """Iterates upwards through a hierarchy and returns the first creator.

    Iterates up through an archival object's ancestors looking for linked agents,
    then iterates over the linked agents to see if it contains an agent with
    the role of creator. Returns the first creator it finds."""
    for ancestor in get_ancestors(obj):
        if len([c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]):
            return [c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]
    return []


def get_date_string(dates):
    date_strings = []
    for date in dates:
        if date.get("expression"):
            date_strings.append(date["expression"])
        elif date.get("end"):
            date_strings.append("{}-{}".format(date["begin"], date["end"]))
        else:
            date_strings.append(date["begin"])
    return ", ".join(date_strings)


def combine_references(object):
    """Adds type and title fields to references, then removes unneeded resolved objects."""
    for key, type_key in (["ancestors", None], ["children", None], ["subjects", "term_type"], ["linked_agents", "agent_type"]):
        for obj in object.get(key, []):
            if obj.get("_resolved"):
                type = "collection"
                if key == "subjects":
                    type = obj["_resolved"]["terms"][0][type_key]
                elif key == "linked_agents":
                    type = obj["_resolved"][type_key]
                if obj["_resolved"].get("subjects"):
                    obj["subjects"] = combine_references(obj["_resolved"])["subjects"]
                obj["type"] = type
                obj["title"] = obj["_resolved"].get("title", obj["_resolved"].get("display_string"))
                obj["dates"] = get_date_string(obj["_resolved"].get("dates", []))
                del obj["_resolved"]
    return object


def add_group(object, aspace_client):
    """Adds group object, with data about the highest-level collection containing this object."""

    top_ancestor = object
    if object.get("ancestors"):
        last_ancestor = object["ancestors"][-1]
        top_ancestor = last_ancestor["_resolved"] if last_ancestor.get("_resolved") else aspace_client.get(
            last_ancestor.get("archivesspace_uri", last_ancestor.get("ref")),
            params={"resolve": ["linked_agents", "subjects"]}).json()

    group_obj = combine_references(top_ancestor)

    creators = [a for a in group_obj.get("linked_agents", []) if a["role"] == "creator"]
    if object["jsonmodel_type"].startswith("agent_"):
        creators = [{"ref": object["uri"], "role": "creator", "type": object["jsonmodel_type"], "title": object["title"]}]

    object["group"] = {
        "identifier": group_obj.get("ref", group_obj.get("uri")),
        "creators": creators,
        "dates": group_obj.get("dates", group_obj.get("dates_of_existence", [])),
        "title": group_obj.get("title"),
    }
    return object


def handle_cartographer_reference(reference):
    reference["ref"] = reference["archivesspace_uri"]
    reference["type"] = "collection"
    del reference["archivesspace_uri"]
    return reference


class ArchivesSpaceHelper:
    def __init__(self, aspace):
        self.aspace = aspace if aspace else instantiate_aspace(settings.ARCHIVESSPACE)

    def has_children(self, uri):
        """Checks whether an archival object has children using the tree/node endpoint.
        Checks the child_count attribute and if the value is greater than 0, return true, otherwise return False."""
        obj = self.aspace.client.get(uri).json()
        resource_uri = obj['resource']['ref']
        tree_node = self.aspace.client.get('{}/tree/node?node_uri={}'.format(resource_uri, obj['uri'])).json()
        return True if tree_node['child_count'] > 0 else False

    def tree_children(self, waypoint_count, base_uri, params):
        """Returns immediate children of a resource or archival_object.

        In cases where children don't have titles (for example, only a date) the
        date expression for the first date object is returned.
        """
        children = []
        for i in range(waypoint_count):
            params["offset"] = i
            waypoint = self.aspace.client.get("{}/tree/waypoint".format(base_uri), params=params).json()
            for child in waypoint:
                title = child["title"] if child["title"] else get_date_string(child["dates"])
                children.append({
                    "title": title,
                    "ref": child["uri"],
                    "level": child["level"],
                    "order": child["position"],
                    "dates": get_date_string(child.get("dates", [])),
                    "type": "collection" if child["child_count"] > 0 else "object"})
        return children

    def get_resource_children(self, uri):
        tree_root = self.aspace.client.get(
            "{}/tree/root".format(uri.rstrip("/"))).json()
        params = {"offset": 0}
        return self.tree_children(tree_root["waypoints"], uri, params) if tree_root["child_count"] > 0 else []

    def get_archival_object_children(self, resource_uri, object_uri):
        tree_node = self.aspace.client.get(
            "{}/tree/node?node_uri={}".format(resource_uri, object_uri)).json()
        params = {"offset": 0, "parent_node": object_uri}
        return self.tree_children(tree_node["waypoints"], resource_uri, params)
