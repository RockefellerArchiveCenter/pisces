from fetcher.helpers import instantiate_aspace
from pisces import settings


class ArchivesSpaceHelper:
    def __init__(self):
        self.aspace = instantiate_aspace(settings.ARCHIVESSPACE)

    def closest_parent_value(self, uri, key):
        """Iterates up through an archival object's ancestors looking for the
        first value in a particular field. Returns that value."""
        obj = self.aspace.client.get(uri).json()
        for a in obj['ancestors']:
            ancestor = self.aspace.client.get(a['ref']).json()
            if ancestor.get(key) not in ['', [], {}, None]:
                return ancestor[key]

    def has_children(self, uri):
        """Checks whether an archival object has children using the tree/node endpoint.
        Checks the child_count attribute and if the value is greater than 0, return true, otherwise return False."""
        obj = self.aspace.repo.archival_objects(int(uri.split('/')[4]))
        resource_id = obj.resource.ref
        try:
            tree_node = self.aspace.client.get(resource_id + '/tree/node?node_uri=' + uri).json()
            return True if tree_node['child_count'] > 0 else False
        except KeyError:
            return False
