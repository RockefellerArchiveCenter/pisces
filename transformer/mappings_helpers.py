from asnake.aspace import ASpace

from pisces import settings


class ArchivesSpaceHelper:
    def __init__(self):
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             user=settings.ARCHIVESSPACE['user'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if type(self.repo) == dict and 'error' in self.repo:
            raise ArchivesSpaceDataFetcherError(self.repo['error'])

    def closest_parent_value(self, uri, key):
        """Iterates up through an archival object's ancestors looking for the
        first value in a particular field. Returns that value."""
        obj = self.aspace.client.get(uri)
        if obj.status_code != 200:
            raise Exception("Error getting {} from ArchivesSpace: {}".format(uri, obj.json()['error']))
        for a in obj.ancestors:
            try:
                if getattr(a, key) not in ['', [], {}, None]:
                    return getattr(a, key)
            except AttributeError:
                continue
