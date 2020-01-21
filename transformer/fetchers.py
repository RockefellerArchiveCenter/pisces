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
class WikidataDataFetcherError(Exception): pass
class WikipediaDataFetcherError(Exception): pass


class ArchivesSpaceDataFetcher:
    def __init__(self, object_type=None, action=None, identifier=None):
        self.identifier = identifier
        self.aspace = ASpace(baseurl=settings.ARCHIVESSPACE['baseurl'],
                             user=settings.ARCHIVESSPACE['user'],
                             password=settings.ARCHIVESSPACE['password'])
        self.repo = self.aspace.repositories(settings.ARCHIVESSPACE['repo'])
        if type(self.repo) == dict and 'error' in self.repo:
            raise ArchivesSpaceDataFetcherError(self.repo['error'])

    def changes(self, object_type):
        if object_type in ['resource', 'subject', 'archival_object', 'person', 'organization', 'family']:
            self.object_type = object_type
        else:
            raise ArchivesSpaceDataFetcherError("Unknown object type {}".format(object_type))
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.ARCHIVESSPACE, object_type=self.object_type)
        try:
            data = {'source': 'archivesspace', 'updated': [], 'deleted': []}
            # # TODO: we don't need to fetch this every time
            for d in self.aspace.client.get_paged("delete-feed", params={"modified_since": str(self.last_run)}):
                data['deleted'].append(d)
            for u in self.updated_list(self.object_type):
                if u.publish:
                    data['updated'].append(u.uri)
                else:
                    data['deleted'].append(u.uri)
            self.current_run.status = FetchRun.FINISHED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            return data
        except Exception as e:
            self.current_run.status = FetchRun.ERRORED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            raise ArchivesSpaceDataFetcherError(str(e))

    def updated_list(self, object_type):
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
    def __init__(self):
        self.client = ElectronBond(baseurl=settings.CARTOGRAPHER['baseurl'], user=settings.CARTOGRAPHER['user'], password=settings.CARTOGRAPHER['password'])
        try:
            resp = self.client.get('/status/health/')
            if not resp.status_code:
                raise CartographerDataFetcherError("Cartographer status endpoint is not available. Service may be down.")
        except Exception as e:
            raise CartographerDataFetcherError("Cartographer is not available.")

    def changes(self):
        self.last_run = (int(FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).order_by('-start_time')[0].start_time.timestamp())
                         if FetchRun.objects.filter(status=FetchRun.FINISHED, source=FetchRun.CARTOGRAPHER).exists()
                         else 0)
        self.current_run = FetchRun.objects.create(status=FetchRun.STARTED, source=FetchRun.CARTOGRAPHER)
        try:
            data = {'source': 'cartographer', 'updated': [], 'deleted': []}
            for map in self.client.get('/api/maps/', params={"modified_since": self.last_run}).json()['results']:
                # TODO: make sure publish key is available in Cartographer list view
                # TODO: make sure I'm getting the right URI, could also be `ref`
                if map.get('publish'):
                    data['updated'].append(map.get('ref'))
                else:
                    data['deleted'].append(map.get('ref'))
            for uri in self.client.get('/api/delete-feed/', params={"deleted_since": self.last_run}).json()['results']:
                data['deleted'].append(uri)
            self.current_run.status = FetchRun.FINISHED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            return data
        except Exception as e:
            self.current_run.status = FetchRun.ERRORED
            self.current_run.end_time = timezone.now()
            self.current_run.save()
            raise CartographerDataFetcherError(e)

    # TODO: will probably need some other functions here...


# TODO: need to rethink this - provide a URI to fetch data for??
class WikidataDataFetcher:
    def __init__(self):
        self.client = wd_client()

    def fetch_data(self, identifier):
        try:
            return self.client.get(identifier, load=True).data
        except Exception as e:
            raise WikidataDataFetcherError(e)


# TODO: need to rethink this - provide a URI to fetch data for??
class WikipediaDataFetcher:
    def __init__(self):
        self.client = Wikipedia('en')

    def fetch_data(self, identifier):
        try:
            agent_page = self.client.page(identifier)
            return agent_page.summary
        except Exception as e:
            raise WikipediaDataFetcherError(e)
