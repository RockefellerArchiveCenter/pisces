from asnake.aspace import ASpace
from django.utils import timezone
from electronbonder.client import ElectronBond

from .models import FetchRun, FetchRunError
from .helpers import last_run_time
from pisces import settings


class ArchivesSpaceDataFetcherError:
    pass


class CartographerDataFetcherError:
    pass


class ArchivesSpaceDataFetcher:
    def __init__(self):
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             username=settings.ARCHIVESSPACE['username'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if isinstance(self.repo, dict) and 'error' in self.repo:
            raise ArchivesSpaceDataFetcherError(self.repo['error'])

    def fetch(self, status, object_type):
        current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=FetchRun.ARCHIVESSPACE,
            object_type=object_type)
        last_run = last_run_time(FetchRun.ARCHIVESSPACE, object_type)
        try:
            fetched = getattr(self, "get_{}".format(status))(object_type, last_run)
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
                message=e,
            )

    def get_updated(self, object_type, last_run):
        data = []
        for u in self.updated_list(object_type, last_run):
            if u.publish:
                # POST it
                data.append(u.uri)
        return data

    def get_deleted(self, object_type, last_run):
        data = []
        last_run = last_run_time(object_type)
        for d in self.aspace.client.get_paged(
                "delete-feed", params={"modified_since": str(last_run)}):
            # POST it
            data.append(d)
        for u in self.updated_list(object_type, last_run):
            if not u.publish:
                # POST it
                data.append(u.uri)
        return data

    def updated_list(self, object_type, last_run):
        if object_type == 'resource':
            return self.repo.resources.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'archival_object':
            return self.repo.archival_objects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'subject':
            return self.aspace.subjects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'person':
            return self.aspace.agents["people"].with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'organization':
            return self.aspace.agents["corporate_entities"].with_params(
                all_ids=True, modified_since=last_run)
        elif self.object_type == 'family':
            return self.aspace.agents["families"].with_params(
                all_ids=True, modified_since=last_run)


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

    def fetch(self, status, object_type):
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        last_run = last_run_time(FetchRun.CARTOGRAPHER, object_type)
        try:
            fetched = getattr(self, "get_{}".format(status))(last_run)
            self.current_run.status = FetchRun.FINISHED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            return fetched
        except Exception as e:
            current_run.status = FetchRun.ERRORED
            current_run.end_time = timezone.now()
            current_run.save()
            FetchRunError.objects.create(
                run=current_run,
                message=e,
            )

    def get_updated(self, last_run):
        data = []
        for map in self.client.get(
                '/api/maps/', params={"modified_since": last_run}).json()['results']:
            if map.get('publish'):
                map_data = self.client.get(map['ref']).json()
                data.append(map_data)
        return data

    def get_deleted(self):
        data = []
        for map in self.client.get(
                '/api/maps/', params={"modified_since": last_run}).json()['results']:
            if not map.get('publish'):
                map_data = self.client.get(map['ref']).json()
                data.append(map_data)
        for uri in self.client.get(
                '/api/delete-feed/', params={"deleted_since": self.last_run}).json()['results']:
            data.append(uri)
        return data
