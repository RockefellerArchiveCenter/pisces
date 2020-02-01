from asnake.aspace import ASpace
from django.utils import timezone
from electronbonder.client import ElectronBond

from .models import FetchRun, FetchRunError
from .helpers import last_run_time, send_post_request
from pisces import settings


class FetcherError(Exception):
    pass


class BaseDataFetcher:
    """
    Base data fetcher class which provides a common run method inherited by other
    fetchers. Requires a source attribute to be set on inheriting fetchers.
    """

    def fetch(self, status, object_type, post_service_url):
        current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=self.source,
            object_type=object_type)
        last_run = last_run_time(self.source, object_type)
        try:
            fetched = getattr(
                self, "get_{}".format(status))(
                object_type, last_run, post_service_url)
            current_run.status = FetchRun.FINISHED
            current_run.end_time = timezone.now()
            current_run.save()
            return fetched
        except Exception as e:
            current_run.status = FetchRun.ERRORED
            current_run.end_time = timezone.now()
            current_run.save()
            FetchRunError.objects.create(
                run=current_run,
                message=str(e),
            )
            raise FetcherError("Error fetching data: {}".format(e))


class ArchivesSpaceDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from ArchivesSpace."""

    def __init__(self):
        self.source = FetchRun.ARCHIVESSPACE
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             username=settings.ARCHIVESSPACE['username'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if isinstance(self.repo, dict) and 'error' in self.repo:
            raise FetcherError(self.repo['error'])

    def get_updated(self, object_type, last_run, post_service_url):
        data = []
        for u in self.updated_list(object_type, last_run, True):
            send_post_request(post_service_url, u.json())
            data.append(u.uri)
        return data

    def get_deleted(self, object_type, last_run, post_service_url):
        data = []
        for d in self.deleted_list(object_type, last_run):
            send_post_request(post_service_url, d)
            data.append(d)
        for u in self.updated_list(object_type, last_run, False):
            send_post_request(post_service_url, u.uri)
            data.append(u.uri)
        return data

    def updated_list(self, object_type, last_run, publish):
        if object_type == 'resource':
            list = self.repo.resources.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'archival_object':
            list = self.repo.archival_objects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'subject':
            list = self.aspace.subjects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'person':
            list = self.aspace.agents["people"].with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'organization':
            list = self.aspace.agents["corporate_entities"].with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'family':
            list = self.aspace.agents["families"].with_params(
                all_ids=True, modified_since=last_run)
        for obj in list:
            if obj.publish == publish:
                yield obj

    def deleted_list(self, object_type, last_run):
        for d in self.aspace.client.get_paged(
                "delete-feed", params={"modified_since": str(last_run)}):
            if object_type in d:
                yield d


class CartographerDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from Cartographer."""

    def __init__(self):
        self.source = FetchRun.CARTOGRAPHER
        self.client = ElectronBond(
            baseurl=settings.CARTOGRAPHER['baseurl'],
            user=settings.CARTOGRAPHER['user'],
            password=settings.CARTOGRAPHER['password'])
        try:
            resp = self.client.get('/status/health/')
            if not resp.status_code:
                raise FetcherError(
                    "Cartographer status endpoint is not available. Service may be down.")
        except Exception:
            raise FetcherError(
                "Cartographer is not available.")

    def get_updated(self, object_type, last_run, post_service_url):
        data = []
        for map in self.updated_list(last_run, True):
            map_data = self.client.get(map.get('ref')).json()
            send_post_request(post_service_url, map_data)
            data.append(map.get('ref'))
        return data

    def get_deleted(self, object_type, last_run, post_service_url):
        data = []
        for map in self.updated_list(last_run, False):
            send_post_request(post_service_url, map.get('ref'))
            data.append(map.get('ref'))
        for uri in self.deleted_list(last_run):
            send_post_request(post_service_url, uri)
            data.append(uri)
        return data

    def updated_list(self, last_run, publish):
        for map in self.client.get(
                '/api/maps/', params={"modified_since": last_run}).json()['results']:
            if map.get('publish') == publish:
                yield map

    def deleted_list(self, last_run):
        for uri in self.client.get(
                '/api/delete-feed/', params={"deleted_since": last_run}).json()['results']:
            yield uri
