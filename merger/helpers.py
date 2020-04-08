from fetcher.helpers import instantiate_aspace
from pisces import settings
from silk.profiling.profiler import silk_profile


class ArchivesSpaceHelper:
    def __init__(self):
        self.aspace = instantiate_aspace(settings.ARCHIVESSPACE, repo=False)

    @silk_profile()
    def get_ancestors(self, uri):
        """Returns the full record for each ancestor."""
        obj = self.aspace.client.get(uri).json()
        for a in obj['ancestors']:
            yield self.aspace.client.get(a['ref']).json()

    @silk_profile()
    def closest_parent_value(self, uri, key):
        """Iterates up through an archival object's ancestors looking for the
        first value in a particular field. Returns that value."""
        for ancestor in self.get_ancestors(uri):
            if ancestor.get(key) not in ['', [], {}, None]:
                return ancestor[key]

    @silk_profile()
    def closest_creators(self, uri):
        """Iterates up through an archival object's ancestors looking for linked agents.
        Iterates over the linked agents list while checking if there is a creator using
        the length of the role. Returns the first creator it finds."""
        for ancestor in self.get_ancestors(uri):
            if len([c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]):
                return [c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]
        return []

    @silk_profile()
    def has_children(self, uri):
        """Checks whether an archival object has children using the tree/node endpoint.
        Checks the child_count attribute and if the value is greater than 0, return true, otherwise return False."""
        obj = self.aspace.client.get(uri).json()
        resource_uri = obj['resource']['ref']
        tree_node = self.aspace.client.get('{}/tree/node?node_uri={}'.format(resource_uri, obj['uri'])).json()
        return True if tree_node['child_count'] > 0 else False

    @silk_profile()
    def get_resource_children(self, uri):
        children = []
        as_tree = self.aspace.client.get("{}/tree".format(uri.rstrip("/"))).json()
        for child in as_tree.get("children"):
            children.append({
                "title": child["title"],
                "ref": child["record_uri"],
                "level": child["level"],
                "type": "collection" if child["has_children"] else "object",
                "identifier": child["id"]})
        return children

    @silk_profile()
    def get_archival_object_children(self, resource_uri, object_uri):
        children = []
        tree_node = self.aspace.client.get(
            "{}/tree/node?node_uri={}".format(resource_uri, object_uri)).json()
        for idx in tree_node["precomputed_waypoints"].get(object_uri):
            for child in tree_node["precomputed_waypoints"].get(object_uri)[idx]:
                children.append({
                    "title": child["title"],
                    "ref": child["uri"],
                    "level": child["level"],
                    "order": child["position"],
                    "type": "collection" if child["child_count"] > 0 else "object",
                    "identifier": child["uri"].rstrip("/").split("/")[-1]})
        return children
