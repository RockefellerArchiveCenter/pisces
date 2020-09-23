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


def get_description(notes):
    """Gets text from all published Scope and Contents notes."""
    description_strings = []
    for note in [n for n in notes if all([n.get("type") == "scopecontent", n["publish"]])]:
        description_strings += [sn.get("content", "") for sn in note.get("subnotes")]
    return ", ".join(description_strings)


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
                obj["description"] = get_description(obj["_resolved"].get("notes", []))
                del obj["_resolved"]
    return object


def add_group(object):
    """Adds group object, with data about the highest-level collection containing this object."""

    top_ancestor = object["ancestors"][-1]["_resolved"] if object.get("ancestors") else object
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

    def tree_children(self, list, key):
        """Returns immediate children of a resource or archival_object.

        In cases where children don't have titles (for example, only a date) the
        date expression for the first date object is returned.
        """
        children = []
        for idx in list["precomputed_waypoints"].get(key):
            for child in list["precomputed_waypoints"].get(key)[idx]:
                resolved = self.aspace.client.get(child["uri"]).json()
                children.append({
                    "title": resolved.get("title", resolved.get("display_string")),
                    "ref": child["uri"],
                    "level": child["level"],
                    "order": child["position"],
                    "dates": get_date_string(resolved.get("dates", [])),
                    "description": get_description(resolved.get("notes", [])),
                    "type": "collection" if child["child_count"] > 0 else "object"})
        return children

    def get_resource_children(self, uri):
        tree_root = self.aspace.client.get(
            "{}/tree/root".format(uri.rstrip("/"))).json()
        return self.tree_children(tree_root, "") if tree_root["child_count"] > 0 else []

    def get_archival_object_children(self, resource_uri, object_uri):
        tree_node = self.aspace.client.get(
            "{}/tree/node?node_uri={}".format(resource_uri, object_uri)).json()
        return self.tree_children(tree_node, object_uri)

    def resolve_cartographer_ancestor(self, ancestor):
        resolved = self.aspace.client.get(
            ancestor["archivesspace_uri"],
            params={"resolve": ["linked_agents", "subjects"]}).json()
        ancestor["ref"] = ancestor["archivesspace_uri"]
        ancestor["_resolved"] = combine_references(resolved)
        del ancestor["archivesspace_uri"]
        return ancestor
