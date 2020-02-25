from datetime import datetime

import vcr
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from .fetchers import ArchivesSpaceDataFetcher, CartographerDataFetcher
from .helpers import last_run_time
from .models import FetchRun, FetchRunError
from .views import (ArchivesSpaceDeletesView, ArchivesSpaceUpdatesView,
                    CartographerDeletesView, CartographerUpdatesView)

archivesspace_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/fetcher',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

cartographer_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/fetcher',
    record_mode='once',
    match_on=['path', 'method'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)


class FetcherTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        time = datetime(2020, 2, 1)
        for object_type in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES:
            f = FetchRun.objects.create(
                status=FetchRun.FINISHED,
                source=FetchRun.ARCHIVESSPACE,
                object_type=object_type[0]
            )
            f.start_time = time
            f.save()

    def test_fetchers(self):
        for object_type_choices, fetcher, fetcher_vcr, cassette_prefix in [
                (FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES, ArchivesSpaceDataFetcher, archivesspace_vcr, "ArchivesSpace"),
                (FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES, CartographerDataFetcher, cartographer_vcr, "Cartographer")]:
            for status in ["updated", "deleted"]:
                for object_type in object_type_choices:
                    with fetcher_vcr.use_cassette("{}-{}-{}.json".format(cassette_prefix, status, object_type[0])):
                        list = fetcher().fetch(status, object_type[0])
                        for obj in list:
                            self.assertTrue(isinstance(obj, str))
            self.assertTrue(len(FetchRun.objects.all()), len(object_type_choices) * 2)
            self.assertEqual(len(FetchRunError.objects.all()), 0)

    def test_views(self):
        for view, status, url_name, object_type_choices, fetcher_vcr, cassette_prefix in [
                (ArchivesSpaceDeletesView, "deleted", "fetch-archivesspace-deletes", FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES, archivesspace_vcr, "ArchivesSpace"),
                (ArchivesSpaceUpdatesView, "updated", "fetch-archivesspace-updates", FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES, archivesspace_vcr, "ArchivesSpace"),
                (CartographerDeletesView, "updated", "fetch-cartographer-deletes", FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES, cartographer_vcr, "Cartographer"),
                (CartographerUpdatesView, "updated", "fetch-cartographer-updates", FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES, cartographer_vcr, "Cartographer")]:
            for object_type in object_type_choices:
                with fetcher_vcr.use_cassette("{}-{}-{}.json".format(cassette_prefix, status, object_type[0])):
                    request = self.factory.post("{}?object_type={}".format(reverse(url_name), object_type[0]))
                    response = view().as_view()(request)
                    self.assertEqual(response.status_code, 200, "Request error: {}".format(response.data))

    def test_last_run(self):
        for source in FetchRun.SOURCE_CHOICES:
            for object in getattr(FetchRun, "{}_OBJECT_TYPE_CHOICES".format(source[1].upper())):
                last_run = last_run_time(source, object)
                self.assertEqual(last_run, 0)
                time = timezone.now()
                FetchRun.objects.create(
                    status=FetchRun.FINISHED,
                    source=source,
                    object_type=object,
                    end_time=time)
                updated_last_run = last_run_time(source, object)
                self.assertEqual(updated_last_run, int(time.timestamp()))
