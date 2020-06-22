import asyncio
from datetime import datetime
from itertools import chain, islice

from django.utils import timezone
from merger.mergers import (AgentMerger, ArchivalObjectMerger,
                            ArrangementMapMerger, ResourceMerger,
                            SubjectMerger)
from pisces import settings
from silk.profiling.profiler import silk_profile
from transformer.transformers import Transformer

from .helpers import (handle_deleted_uri, instantiate_aspace,
                      instantiate_electronbond, last_run_time,
                      send_error_notification)
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
        clients = self.instantiate_clients(object_type)
        processed = 0
        merger = self.get_merger(object_type)
        try:
            print("Starting Fetch")
            fetched = getattr(
                self, "get_{}".format(object_status))(
                clients, object_type, last_run, current_run)
            print("Fetch finished")
        except Exception as e:
            current_run.status = FetchRun.ERRORED
            current_run.end_time = timezone.now()
            current_run.save()
            FetchRunError.objects.create(
                run=current_run,
                message="Error fetching data: {}".format(e),
            )
            raise FetcherError(e)

        print("Calling async.io")
        for n, chunk in enumerate(self.chunks(fetched, settings.CHUNK_SIZE)):
            print("Chunk {}".format(n), datetime.now())
            asyncio.get_event_loop().run_until_complete(
                self.process_fetched_list(
                    chunk, merger, processed, object_type, clients, current_run))

        current_run.status = FetchRun.FINISHED
        current_run.end_time = timezone.now()
        current_run.save()
        if current_run.error_count > 0:
            send_error_notification(current_run)
        return processed

    def instantiate_clients(self, object_type):
        repo = True if object_type in ["resource", "archival_object"] else False
        return {
            "aspace": instantiate_aspace(settings.ARCHIVESSPACE, repo=repo),
            "cartographer": instantiate_electronbond(settings.CARTOGRAPHER)
        }

    def chunks(self, iterable, size):
        iterator = iter(iterable)
        for first in iterator:
            yield chain([first], islice(iterator, size - 1))

    async def process_fetched_list(self, fetched, merger, processed, object_type, clients, current_run):
        tasks = []
        for obj in fetched:
            task = asyncio.ensure_future(self.process_obj(obj, merger, processed, object_type, clients, current_run))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_obj(self, obj, merger, processed, object_type, clients, current_run):
        try:
            merged, merged_object_type = await merger(clients).merge(object_type, obj.json())
            await Transformer().run(merged_object_type, merged)
            processed += 1
        except Exception as e:
            FetchRunError.objects.create(run=current_run, message=str(e))


class ArchivesSpaceDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from ArchivesSpace."""
    source = FetchRun.ARCHIVESSPACE

    def get_merger(self, object_type):
        MERGERS = {
            "resource": ResourceMerger,
            "archival_object": ArchivalObjectMerger,
            "subject": SubjectMerger,
            "agent_person": AgentMerger,
            "agent_corporate_entity": AgentMerger,
            "agent_family": AgentMerger,
        }
        return MERGERS[object_type]

    @silk_profile()
    def get_updated(self, clients, object_type, last_run, current_run):
        return self.updated_list(clients["aspace"], object_type, last_run, True)

    @silk_profile()
    def get_deleted(self, clients, object_type, last_run, current_run):
        data = []
        aspace = clients["aspace"]
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

    def get_merger(self, object_type):
        return ArrangementMapMerger

    @silk_profile()
    def get_updated(self, clients, object_type, last_run, current_run):
        return self.updated_list(clients["cartographer"], last_run, True)

    @silk_profile()
    def get_deleted(self, clients, object_type, last_run, current_run):
        data = []
        for component in self.updated_list(clients["cartographer"], last_run, False):
            updated = handle_deleted_uri(component.get("ref"), self.source, object_type, current_run)
            if updated:
                data.append(updated)
        for uri in self.deleted_list(clients["cartographer"], last_run):
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
