from django.utils import timezone
from electronbonder.client import ElectronBond
from pisces import settings

from .helpers import instantiate_aspace, last_run_time, send_post_request
from .models import FetchRun, FetchRunError


class FetcherError(Exception):
    pass


class BaseDataFetcher:
    """
    Base data fetcher class which provides a common run method inherited by other
    fetchers. Requires a source attribute to be set on inheriting fetchers.
    """

    def fetch(self, object_status, object_type):
        current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=self.source,
            object_type=object_type,
            object_status=object_status)
        last_run = last_run_time(self.source, object_status, object_type)
        try:
            fetched = getattr(
                self, "get_{}".format(object_status))(
                object_type, last_run, current_run)
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
        self.aspace = instantiate_aspace(settings.ARCHIVESSPACE)
        self.transform_url = settings.ARCHIVESSPACE["transform_url"]

    def get_updated(self, object_type, last_run, current_run):
        data = []
        for u in self.updated_list(object_type, last_run, True):
            delivered = send_post_request(self.transform_url, u.json(), current_run)
            if delivered:
                data.append(u.uri)
        return data

    def get_deleted(self, object_type, last_run, current_run):
        data = []
        for d in self.deleted_list(object_type, last_run):
            delivered = send_post_request(self.transform_url, d, current_run)
            if delivered:
                data.append(d)
        for u in self.updated_list(object_type, last_run, False):
            delivered = send_post_request(self.transform_url, u.uri, current_run)
            if delivered:
                data.append(u.uri)
        return data

    def updated_list(self, object_type, last_run, publish):
        if object_type == 'resource':
            list = self.aspace.repo.resources.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'archival_object':
            list = self.aspace.repo.archival_objects.with_params(
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
                if not(obj.jsonmodel_type == "resource" and obj.id_0.startswith("LI")):
                    yield obj

    def deleted_list(self, object_type, last_run):
        for d in self.aspace.client.get_paged(
                "delete-feed", params={"modified_since": str(last_run)}):
            if object_type in d:
                yield d


class CartographerDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from Cartographer."""

    def __init__(self):
        self.transform_url = settings.CARTOGRAPHER["transform_url"]
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

    def get_updated(self, object_type, last_run, current_run):
        data = []
        for map in self.updated_list(last_run, True):
            map_data = self.client.get(map.get('ref')).json()
            delivered = send_post_request(self.transform_url, map_data, current_run)
            if delivered:
                data.append(map.get('ref'))
        return data

    def get_deleted(self, object_type, last_run, current_run):
        data = []
        for map in self.updated_list(last_run, False):
            delivered = send_post_request(self.transform_url, map.get('ref'), current_run)
            if delivered:
                data.append(map.get('ref'))
        for uri in self.deleted_list(last_run):
            delivered = send_post_request(self.transform_url, uri, current_run)
            if delivered:
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
