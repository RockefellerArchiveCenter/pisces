from django.utils import timezone
from pisces import settings
from silk.profiling.profiler import silk_profile

from .helpers import (handle_deleted_uri, instantiate_aspace,
                      instantiate_electronbond, last_run_time,
                      send_post_request)
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
            client = self.instantiate_client(object_type)
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

    def instantiate_client(self, object_type):
        repo = True if object_type in ["resource", "archival_object"] else False
        return instantiate_aspace(settings.ARCHIVESSPACE, repo=repo)

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
            updated = handle_deleted_uri(d, self.source, object_type, current_run)
            if updated:
                data.append(updated)
        for u in self.updated_list(aspace, object_type, last_run, False):
            updated = handle_deleted_uri(u.uri, self.source, object_type, current_run)
            if updated:
                data.append(updated)
        return data

    @silk_profile()
    def get_archival_objects(self, aspace, last_run, publish):
        """Returns only archival objects belonging to a published resource."""
        for obj in aspace.repo.archival_objects.with_params(
                all_ids=True, modified_since=last_run):
            if not obj.has_unpublished_ancestor:
                yield obj

    @silk_profile()
    def get_resources(self, aspace, last_run):
        """Return only resources whose id_0 attribute starts with 'FA'"""
        for obj in aspace.repo.resources.with_params(
                all_ids=True, modified_since=last_run):
            if obj.id_0.startswith("FA"):
                yield obj

    @silk_profile()
    def updated_list(self, aspace, object_type, last_run, publish):
        if object_type == 'resource':
            list = self.get_resources(aspace, last_run)
        elif object_type == 'archival_object':
            list = self.get_archival_objects(aspace, last_run, publish)
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

    def instantiate_client(self, object_type):
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
            updated = handle_deleted_uri(component.get("ref"), self.source, object_type, current_run)
            if updated:
                data.append(updated)
        for uri in self.deleted_list(client, last_run):
            updated = handle_deleted_uri(uri, self.source, object_type, current_run)
            if updated:
                data.append(updated)
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
