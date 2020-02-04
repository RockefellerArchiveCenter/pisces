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
