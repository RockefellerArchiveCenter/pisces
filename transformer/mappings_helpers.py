from asnake.aspace import ASpace
from fetcher.fetchers import FetcherError
from pisces import settings


class ArchivesSpaceHelper:
    def __init__(self):
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             username=settings.ARCHIVESSPACE['username'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if isinstance(self.repo, dict) and 'error' in self.repo:
            raise FetcherError(self.repo['error'])

    def closest_parent_value(self, uri, key):
        """Iterates up through an archival object's ancestors looking for the
        first value in a particular field. Returns that value."""
        obj = self.aspace.client.get(uri).json()
        for a in obj['ancestors']:
            ancestor = self.aspace.client.get(a['ref']).json()
            if ancestor.get(key) not in ['', [], {}, None]:
                return ancestor[key]
