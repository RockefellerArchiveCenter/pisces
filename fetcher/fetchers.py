import asyncio
from concurrent.futures import ThreadPoolExecutor

from django.utils import timezone
from merger.mergers import (AgentMerger, ArchivalObjectMerger,
                            ArrangementMapMerger, ResourceMerger,
                            SubjectMerger)
from pisces import settings
from transformer.transformers import Transformer

from .helpers import (handle_deleted_uris, instantiate_aspace,
                      instantiate_electronbond, last_run_time,
                      send_error_notification)
from .models import FetchRun, FetchRunError


class FetcherError(Exception):
    pass


def run_transformer(merged_object_type, merged):
    Transformer().run(merged_object_type, merged)


def run_merger(merger, object_type, fetched):
    return merger(clients).merge(object_type, fetched)


class BaseDataFetcher:
    """Base data fetcher.

    Provides a common run method inherited by other fetchers. Requires a source
    attribute to be set on inheriting fetchers.
    """

    def fetch(self, object_status, object_type):
        self.object_status = object_status
        self.object_type = object_type
        self.last_run = last_run_time(self.source, object_status, object_type)
        global clients
        clients = self.instantiate_clients()
        self.processed = 0
        self.current_run = FetchRun.objects.create(
            status=FetchRun.STARTED,
            source=self.source,
            object_type=object_type,
            object_status=object_status)
        self.merger = self.get_merger(object_type)

        try:
            fetched = getattr(
                self, "get_{}".format(self.object_status))()
            asyncio.get_event_loop().run_until_complete(
                self.process_fetched(fetched))
        except Exception as e:
            self.current_run.status = FetchRun.ERRORED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            FetchRunError.objects.create(
                run=self.current_run,
                message="Error fetching data: {}".format(e),
            )
            raise FetcherError(e)

        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        if self.current_run.error_count > 0:
            send_error_notification(self.current_run)
        return self.processed

    def instantiate_clients(self):
        return {
            "aspace": instantiate_aspace(settings.ARCHIVESSPACE),
            "cartographer": instantiate_electronbond(settings.CARTOGRAPHER)
        }

    async def process_fetched(self, fetched):
        tasks = []
        to_delete = []
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        semaphore = asyncio.BoundedSemaphore(settings.CHUNK_SIZE)
        for object_id in fetched:
            task = asyncio.ensure_future(self.process_obj(object_id, loop, executor, semaphore, to_delete))
            tasks.append(task)
        tasks.append(asyncio.ensure_future(handle_deleted_uris(to_delete, self.source, self.object_type, self.current_run)))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_obj(self, object_id, loop, executor, semaphore, to_delete):
        async with semaphore:
            try:
                if self.object_status == "updated":
                    fetched = await self.get_obj(object_id)
                    if self.is_exportable(fetched):
                        merged, merged_object_type = await loop.run_in_executor(executor, run_merger, self.merger, self.object_type, fetched)
                        await loop.run_in_executor(executor, run_transformer, merged_object_type, merged)
                    else:
                        to_delete.append(fetched.get("uri", fetched.get("archivesspace_uri")))
                else:
                    to_delete.append(object_id)
                self.processed += 1
            except Exception as e:
                print(e)
                FetchRunError.objects.create(run=self.current_run, message=str(e))

    def is_exportable(self, obj):
        """Determines whether the object can be exported.

        Unpublished objects should not be exported.
        Objects with unpublished ancestors should not be exported.
        Resource records whose id_0 field does not begin with FA should not be exported.
        """
        if not obj.get("publish"):
            return False
        if obj.get("has_unpublished_ancestor"):
            return False
        if obj.get("id_0") and not obj.get("id_0").startswith("FA"):
            return False
        return True


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

    def get_updated(self):
        params = {"all_ids": True, "modified_since": self.last_run}
        endpoint = self.get_endpoint(self.object_type)
        return clients["aspace"].client.get(endpoint, params=params).json()

    def get_deleted(self):
        data = []
        for d in clients["aspace"].client.get_paged(
                "delete-feed", params={"modified_since": str(self.last_run)}):
            if self.get_endpoint(self.object_type) in d:
                data.append(d)
        return data

    def get_endpoint(self, object_type):
        repo_baseurl = "/repositories/{}".format(settings.ARCHIVESSPACE["repo"])
        endpoint = None
        if object_type == 'resource':
            endpoint = "{}/resources".format(repo_baseurl)
        elif object_type == 'archival_object':
            endpoint = "{}/archival_objects".format(repo_baseurl)
        elif object_type == 'subject':
            endpoint = "/subjects"
        elif object_type == 'agent_person':
            endpoint = "/agents/people"
        elif object_type == 'agent_corporate_entity':
            endpoint = "/agents/corporate_entities"
        elif object_type == 'agent_family':
            endpoint = "/agents/families"
        return endpoint

    async def get_obj(self, obj_id):
        aspace = clients["aspace"]
        obj_endpoint = self.get_endpoint(self.object_type)
        obj = aspace.client.get(
            "{}/{}".format(obj_endpoint, obj_id),
            params={"resolve": ["ancestors", "ancestors::linked_agents", "linked_agents", "subjects"]}).json()
        return obj


class CartographerDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from Cartographer."""
    source = FetchRun.CARTOGRAPHER
    base_endpoint = "/api/components/"

    def get_merger(self, object_type):
        return ArrangementMapMerger

    def get_updated(self):
        data = []
        for obj in clients["cartographer"].get(
                self.base_endpoint, params={"modified_since": self.last_run}).json()['results']:
            data.append("{}{}/".format(self.base_endpoint, obj.get("id")))
        return data

    def get_deleted(self):
        data = []
        for deleted_ref in clients["cartographer"].get(
                '/api/delete-feed/', params={"deleted_since": self.last_run}).json()['results']:
            if self.base_endpoint in deleted_ref['ref']:
                data.append(deleted_ref.get('archivesspace_uri'))
        return data

    async def get_obj(self, obj_ref):
        return clients["cartographer"].get(obj_ref).json()
