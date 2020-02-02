import vcr

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from .fetchers import ArchivesSpaceDataFetcher
from .helpers import last_run_time
from .models import FetchRun
from .views import ArchivesSpaceDeletesView, ArchivesSpaceUpdatesView

fetch_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

post_service_url = "http://pisces-web:8007/transform/archivesspace/"


class FetcherTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_archivesspace_fetcher(self):
        for status in ["updated", "deleted"]:
            for object_type in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES:
                with fetch_vcr.use_cassette("ArchivesSpace-{}-{}.yml".format(status, object_type[0])):
                    list = ArchivesSpaceDataFetcher().fetch(status, object_type[0], post_service_url)
                    for obj in list:
                        self.assertTrue(isinstance(obj, str))
        self.assertTrue(len(FetchRun.objects.all()), len(FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES) * 2)

    def test_archivesspace_views(self):
        for view, status, url_name in [
                (ArchivesSpaceDeletesView, "deleted", "fetch-archivesspace-deletes"),
                (ArchivesSpaceUpdatesView, "updated", "fetch-archivesspace-updates")]:
            for object_type in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES:
                with fetch_vcr.use_cassette("ArchivesSpace-{}-{}.yml".format(status, object_type[0])):
                    request = self.factory.post("{}?object_type={}&post_service_url={}".format(reverse(url_name), object_type[0], post_service_url))
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
