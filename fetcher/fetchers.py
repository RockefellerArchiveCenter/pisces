from django.utils import timezone
from pisces import settings
from silk.profiling.profiler import silk_profile

from .helpers import (instantiate_aspace, instantiate_electronbond,
                      last_run_time, send_post_request)
from .models import FetchRun, FetchRunError


class FetcherError(Exception):
    pass


class BaseDataFetcher:
    """Base data fetcher.

    Provides a common run method inherited by other fetchers. Requires a source
    attribute to be set on inheriting fetchers.
    """

    def fetch(self, object_status, object_type):
        current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=self.source,
            object_type=object_type,
            object_status=object_status)
        last_run = last_run_time(self.source, object_status, object_type)
        try:
            client = self.instantiate_client()
            fetched = getattr(
                self, "get_{}".format(object_status))(
                client, object_type, last_run, current_run)
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
    source = FetchRun.ARCHIVESSPACE

    def instantiate_client(self):
        return instantiate_aspace(settings.ARCHIVESSPACE)

    @silk_profile()
    def get_updated(self, aspace, object_type, last_run, current_run):
        data = []
        for u in self.updated_list(aspace, object_type, last_run, True):
            delivered = send_post_request(
                settings.MERGE_URL,
                {"object_type": object_type, "object": u.json()}, current_run)
            if delivered:
                data.append(u.uri)
        return data

    @silk_profile()
    def get_deleted(self, aspace, object_type, last_run, current_run):
        data = []
        for d in self.deleted_list(aspace, object_type, last_run):
            delivered = send_post_request(settings.INDEX_DELETE_URL, d, current_run)
            if delivered:
                data.append(d)
        for u in self.updated_list(aspace, object_type, last_run, False):
            delivered = send_post_request(settings.INDEX_DELETE_URL, u.uri, current_run)
            if delivered:
                data.append(u.uri)
        return data

    @silk_profile()
    def updated_list(self, aspace, object_type, last_run, publish):
        if object_type == 'resource':
            list = aspace.repo.resources.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'archival_object':
            list = aspace.repo.archival_objects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'subject':
            list = aspace.subjects.with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'agent_person':
            list = aspace.agents["people"].with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'agent_corporate_entity':
            list = aspace.agents["corporate_entities"].with_params(
                all_ids=True, modified_since=last_run)
        elif object_type == 'agent_family':
            list = aspace.agents["families"].with_params(
                all_ids=True, modified_since=last_run)
        for obj in list:
            if obj.publish == publish:
                # If the fetched object is a resource, only return if its id_0 starts with FA
                if not(obj.jsonmodel_type == "resource" and not (obj.id_0.startswith("FA"))):
                    yield obj

    @silk_profile()
    def deleted_list(self, aspace, object_type, last_run):
        for d in aspace.client.get_paged(
                "delete-feed", params={"modified_since": str(last_run)}):
            if object_type in d:
                yield d


class CartographerDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from Cartographer."""
    source = FetchRun.CARTOGRAPHER

    def instantiate_client(self):
        return instantiate_electronbond(settings.CARTOGRAPHER)

    @silk_profile()
    def get_updated(self, client, object_type, last_run, current_run):
        data = []
        for component in self.updated_list(client, last_run, True):
            delivered = send_post_request(
                settings.MERGE_URL,
                {"object_type": object_type, "object": component}, current_run)
            if delivered:
                data.append(component.get('ref'))
        return data

    @silk_profile()
    def get_deleted(self, client, object_type, last_run, current_run):
        data = []
        for component in self.updated_list(client, last_run, False):
            delivered = send_post_request(settings.INDEX_DELETE_URL, component.get("ref"), current_run)
            if delivered:
                data.append(component.get('ref'))
        for uri in self.deleted_list(client, last_run):
            delivered = send_post_request(settings.INDEX_DELETE_URL, uri, current_run)
            if delivered:
                data.append(uri)
        return data

    @silk_profile()
    def updated_list(self, client, last_run, publish):
        for component_ref in client.get(
                '/api/components/', params={"modified_since": last_run}).json()['results']:
            component = client.get('/api/components/{}/'.format(component_ref['id'])).json()
            if component.get('publish') == publish:
                yield component

    @silk_profile()
    def deleted_list(self, client, last_run):
        for deleted_ref in client.get(
                '/api/delete-feed/', params={"deleted_since": last_run}).json()['results']:
            if '/api/components/' in deleted_ref['ref']:
                yield deleted_ref['ref']
