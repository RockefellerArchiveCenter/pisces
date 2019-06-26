import os
import objectpath
import json
import requests

from asnake.aspace import ASpace
from django.utils import timezone
from wikipediaapi import Wikipedia
from wikidata.client import Client as wd_client
from electronbonder.client import ElectronBond

from .models import *
from pisces import settings


class ArchivesSpaceDataFetcherError(Exception): pass
class CartographerDataFetcherError(Exception): pass


class ArchivesSpaceDataFetcher:
    def __init__(self, object_type=None, action=None, identifier=None):
        self.identifier = identifier
        if object_type in ['resource', 'subject', 'archival_object', 'person', 'organization', 'family']:
            self.object_type = object_type
        else:
            raise ArchivesSpaceDataFetcherError("Unknown object type {}".format(object_type))
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             user=settings.ARCHIVESSPACE['user'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if type(self.repo) == dict and 'error' in self.repo:
            raise ArchivesSpaceDataFetcherError(self.repo['error'])

    def changes(self):
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type)
        try:
            data = {'source': 'archivesspace', 'updated': [], 'deleted': []}
            # # TODO: we don't need to fetch this every time
            for d in self.aspace.client.get_paged("delete-feed", params={"modified_since": str(self.last_run)}):
                data['deleted'].append(d)
            for u in self.from_list(self.object_type):
                if u.publish:
                    data['updated'].append(u.uri)
                else:
                    data['deleted'].append(u.uri)
            self.current_run.status = FetchRun.FINISHED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            return data
        except Exception as e:
            print(e)
            self.current_run.status = FetchRun.ERRORED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            raise Exception(str(e))

    def from_list(self, object_type):
        if self.object_type == 'resource':
            return self.repo.resources.with_params(all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'archival_object':
            return self.repo.archival_objects.with_params(all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'subject':
            return self.aspace.subjects.with_params(all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'person':
            return self.aspace.agents["people"].with_params(all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'organization':
            return self.aspace.agents["corporate_entities"].with_params(all_ids=True, modified_since=self.last_run)
        elif self.object_type == 'family':
            return self.aspace.agents["families"].with_params(all_ids=True, modified_since=self.last_run)

    def from_uri(self, uri):
        return self.aspace.client.get(uri).json()


class CartographerDataFetcher:
    def __init__(self, target=None):
        self.client = ElectronBond(baseurl=settings.CARTOGRAPHER['baseurl'], user=settings.CARTOGRAPHER['user'], password=settings.CARTOGRAPHER['password'])
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        self.status = FetchRun.FINISHED
        if target in ['updated', 'deleted', None]:
            self.targets = [target] if target else ['updated', 'deleted']
        else:
            raise CartographerDataFetcherError("Unknown target {}".format(target))
        try:
            resp = self.client.get('/status/health/')
            if not resp.status_code:
                raise CartographerDataFetcherError("Cartographer status endpoint is not available. Service may be down.")
        except Exception as e:
            raise CartographerDataFetcherError("Cartographer is not available.")

    def run(self):
        for target in self.targets:
            getattr(self, "get_{}".format(target))()
        self.current_run.status = self.status
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_updated(self):
        for map in self.client.get('/api/maps/', params={"modified_since": self.last_run}).json()['results']:
            try:
                m = self.client.get(map.get('url')).json()
                if m.get('publish'):
                    self.process_map_item(m)
                else:
                    self.delete_data(m.get('ref', m.get('url')))
            except Exception as e:
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Cartographer map: {}".format(e))
                self.status = FetchRun.ERRORED

    def get_deleted(self):
        for object in self.client.get('/api/delete-feed/', params={"deleted_since": self.last_run}).json()['results']:
            try:
                self.delete_data(object)
            except Exception as e:
                FetchRunError.objects.create(run=self.current_run, message="Error deleting {}: {}".format(object.get('ref'), e))
                self.status = FetchRun.ERRORED

    def process_map_item(self, data):
        self.save_data(data)
        if data.get('children'):
            for item in data.get('children'):
                self.process_map_item(item)

    def save_data(self, data):
        identifier = data.get('ref', data.get('url'))
        source = Identifier.ARCHIVESSPACE if 'repositories' in identifier else Identifier.CARTOGRAPHER
        if Collection.objects.filter(identifier__source=source, identifier__identifier=identifier).exists():
            c = Collection.objects.get(identifier__source=source, identifier__identifier=identifier)
            c.source_tree = data
            c.save()
            if SourceData.objects.filter(collection=c, source=Identifier.CARTOGRAPHER).exists():
                sd = SourceData.objects.get(collection=c, source=Identifier.CARTOGRAPHER)
                sd.data = data
                sd.save()
            else:
                SourceData.objects.create(collection=c, source=SourceData.CARTOGRAPHER, data=data)
        else:
            c = Collection.objects.create(source_tree=data)
            SourceData.objects.create(collection=c, source=SourceData.CARTOGRAPHER, data=data)
            Identifier.objects.create(collection=c, source=source, identifier=identifier)

    def delete_data(self, identifier):
        source = Identifier.ARCHIVESSPACE if 'repositories' in identifier else Identifier.CARTOGRAPHER
        if Collection.objects.filter(identifier__source=source, identifier__identifier=identifier).exists():
            Collection.objects.get(identifier__source=source, identifier__identifier=identifier).delete()


class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIDATA)

    def run(self):
        self.get_agents()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIDATA):
            print(agent)
            try:
                wikidata_id = Identifier.objects.get(source=Identifier.WIKIDATA, agent=agent).identifier
                agent_data = self.client.get(wikidata_id, load=True).data
                if SourceData.objects.filter(source=SourceData.WIKIDATA, agent=agent).exists():
                    source_data = SourceData.objects.get(source=SourceData.WIKIDATA, agent=agent)
                    source_data.data = agent_data
                    source_data.save()
                else:
                    SourceData.objects.create(source=SourceData.WIKIDATA, data=agent_data, agent=agent)
            except Exception as e:
                print(e)
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Wikidata data for agent: {}".format(e))


class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.WIKIPEDIA)

    def run(self):
        self.get_agents()
        self.current_run.status = FetchRun.FINISHED
        self.current_run.end_time = timezone.now()
        self.current_run.save()
        return True

    def get_agents(self):
        for agent in Agent.objects.filter(identifier__source=Identifier.WIKIPEDIA):
            try:
                wikipedia_id = Identifier.objects.get(source=Identifier.WIKIPEDIA, agent=agent).identifier
                print(wikipedia_id)
                agent_page = self.client.page(wikipedia_id)
                print(agent_page)
                if SourceData.objects.filter(source=SourceData.WIKIPEDIA, agent=agent).exists():
                    source_data = SourceData.objects.get(source=SourceData.WIKIPEDIA, agent=agent)
                    source_data.data = agent_page.summary
                    source_data.save()
                else:
                    SourceData.objects.create(source=SourceData.WIKIPEDIA, data=agent_page.summary, agent=agent)
            except Exception as e:
                print(e)
                FetchRunError.objects.create(run=self.current_run, message="Error fetching Wikipedia data for agent: {}".format(e))
