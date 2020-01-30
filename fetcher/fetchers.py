from asnake.aspace import ASpace
from django.utils import timezone
from electronbonder.client import ElectronBond

from .models import FetchRun
from .helpers import last_run_time
from pisces import settings


class ArchivesSpaceDataFetcherError:
    pass


class CartographerDataFetcherError:
    pass


class ArchivesSpaceDataFetcher:
    def __init__(self):
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             user=settings.ARCHIVESSPACE['user'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if isinstance(self.repo, dict) and 'error' in self.repo:
            raise ArchivesSpaceDataFetcherError(self.repo['error'])

    def get_updated(self, object_type):
        self.last_run = last_run_time(source, object_type)
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=FetchRun.ARCHIVESSPACE,
            object_type=object_type)
        data = []
        for u in self.updated_list(object_type):
            if u.publish:
                data.append(u.json())
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return data

    def get_deleted(self, object_type):
        self.last_run = helpers.last_run_time(object_type)
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=FetchRun.ARCHIVESSPACE,
            object_type=object_type)
        data = []
        for d in self.aspace.client.get_paged(
                "delete-feed", params={"modified_since": str(self.last_run)}):
            data.append(d)
        for u in self.updated_list(object_type):
            if not u.publish:
                data.append(u.uri)
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return data

    def updated_list(self, object_type):
        if self.object_type == 'resource':
            return self.repo.resources.with_params(
                all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'archival_object':
            return self.repo.archival_objects.with_params(
                all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'subject':
            return self.aspace.subjects.with_params(
                all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'person':
            return self.aspace.agents["people"].with_params(
                all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'organization':
            return self.aspace.agents["corporate_entities"].with_params(
                all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'family':
            return self.aspace.agents["families"].with_params(
                all_ids=True, modified_since=self.last_run)


class CartographerDataFetcher:
    def __init__(self):
        self.client = ElectronBond(
            baseurl=settings.CARTOGRAPHER['baseurl'],
            user=settings.CARTOGRAPHER['user'],
            password=settings.CARTOGRAPHER['password'])
        try:
            resp = self.client.get('/status/health/')
            if not resp.status_code:
                raise CartographerDataFetcherError(
                    "Cartographer status endpoint is not available. Service may be down.")
        except Exception:
            raise CartographerDataFetcherError(
                "Cartographer is not available.")

    def get_updated(self):
        self.last_run = last_run_time(FetchRun.CARTOGRAPHER)
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        data = []
        for map in self.client.get(
                '/api/maps/', params={"modified_since": self.last_run}).json()['results']:
            if map.get('publish'):
                map_data = self.client.get(map['ref']).json()
                data.append(map_data)
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return data

    def get_deleted(self):
        self.last_run = self.last_run_time()
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        data = []
        for map in self.client.get(
                '/api/maps/', params={"modified_since": self.last_run}).json()['results']:
            if not map.get('publish'):
                map_data = self.client.get(map['ref']).json()
                data.append(map_data)
        for uri in self.client.get(
                '/api/delete-feed/', params={"deleted_since": self.last_run}).json()['results']:
            data.append(uri)
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return data
