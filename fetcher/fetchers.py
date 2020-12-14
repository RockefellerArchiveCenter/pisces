import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from django.utils import timezone
from merger.mergers import (AgentMerger, ArchivalObjectMerger,
                            ArrangementMapMerger, ResourceMerger,
                            SubjectMerger)
from pisces import settings
from transformer.transformers import Transformer

from .helpers import (grouper, handle_deleted_uris, instantiate_aspace,
                      instantiate_electronbond, last_run_time,
                      send_error_notification, to_isoformat, to_timestamp)
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
        if self.object_status == "updated":
            semaphore = asyncio.BoundedSemaphore(settings.CHUNK_SIZE / self.page_size)
            async with semaphore:
                for obj in self.get_objects(fetched):
                    task = asyncio.ensure_future(self.process_obj(obj, loop, executor, to_delete))
                    tasks.append(task)
        else:
            to_delete = fetched
        tasks.append(asyncio.ensure_future(handle_deleted_uris(to_delete, self.source, self.object_type, self.current_run)))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_obj(self, data, loop, executor, to_delete):
        try:
            if data.get("has_unpublished_ancestor"):
                merged, merged_object_type = await loop.run_in_executor(executor, run_merger, self.merger, self.object_type, data)
                await loop.run_in_executor(executor, run_transformer, merged_object_type, merged)
            else:
                to_delete.append(data.get("uri", data.get("archivesspace_uri")))
            self.processed += 1
        except Exception as e:
            print(e)
            FetchRunError.objects.create(run=self.current_run, message=str(e))


class ArchivesSpaceDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from ArchivesSpace."""
    source = FetchRun.ARCHIVESSPACE
    page_size = 100

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

    def get_updated(self):
        params = {
            "page": 1,
            "page_size": self.page_size,
            "q": "publish:true",
            "type[]": self.object_type,
            "fields[]": "uri",
            "filter": json.dumps({"query": {"jsonmodel_type": "range_query", "field": "system_mtime", "from": to_isoformat(self.last_run)}})
        }
        if self.object_type == "resource":
            params.update({"q": ["publish:true", "four_part_id:FA*"]})
        for result in clients["aspace"].client.get_paged("/search", params=params):
            yield result["uri"].split("/")[-1]

    def get_deleted(self):
        params = {
            "page": 1,
            "page_size": self.page_size,
            "q": "publish:false",
            "type[]": self.object_type,
            "fields[]": "uri",
            "filter": json.dumps({"query": {"jsonmodel_type": "range_query", "field": "system_mtime", "from": to_isoformat(self.last_run)}})
        }
        for d in clients["aspace"].client.get_paged("/search", params=params):
            yield d["uri"]
        for d in clients["aspace"].client.get_paged(
                "delete-feed", params={"modified_since": to_timestamp(self.last_run)}):
            if self.get_endpoint(self.object_type) in d:
                yield d

    def get_objects(self, id_list):
        for id_chunk in grouper(id_list, 100):
            params = {
                "id_set": id_chunk,
                "resolve": ["ancestors", "ancestors::linked_agents", "instances::top_container", "linked_agents", "subjects"]}
            for obj_data in clients["aspace"].client.get(self.get_endpoint(self.object_type), params=params).json():
                yield obj_data


class CartographerDataFetcher(BaseDataFetcher):
    """Fetches updated and deleted data from Cartographer."""
    source = FetchRun.CARTOGRAPHER
    base_endpoint = "/api/components/"
    page_size = 100

    def get_merger(self, object_type):
        return ArrangementMapMerger

    def get_updated(self):
        yield []

    def get_paged(self, client, url, *args, **kwargs):
        """Get list of json objects from URLs of paged items"""
        params = {"offset": 0, "limit": self.page_size}
        if "params" in kwargs:
            params.update(**kwargs["params"])
            del kwargs["params"]

        current_page = client.get(url, params=params, **kwargs)
        current_json = current_page.json()
        while len(current_json["results"]) > 0:
            for obj in current_json["results"]:
                obj_data = client.get("{}{}/".format(self.base_endpoint, obj.get("id"))).json()
                yield obj_data
            if not current_json.get("next"):
                break
            params["offset"] += self.page_size
            current_page = client.get(current_json.get("next"), params=params)
            current_json = current_page.json()

    def get_objects(self, id_list):
        for obj in self.get_paged(clients["cartographer"], self.base_endpoint, params={"modified_since": to_timestamp(self.last_run)}):
            yield obj
