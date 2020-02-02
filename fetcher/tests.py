import vcr

from django.test import TestCase
from django.utils import timezone

from .fetchers import ArchivesSpaceDataFetcher
from .helpers import last_run_time
from .models import FetchRun

fetch_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

post_url = "http://pisces-web:8007/transform/archivesspace/"


class FetcherTest(TestCase):

    def test_archivesspace_fetcher(self):
        for status in ["updated", "deleted"]:
            for i, object_type in enumerate(FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES):
                with fetch_vcr.use_cassette("ArchivesSpace-{}-{}.yml".format(status, object_type[0])):
                    list = ArchivesSpaceDataFetcher().fetch(status, object_type[0], post_url)
                    for obj in list:
                        self.assertTrue(isinstance(obj, str))
        self.assertTrue(len(FetchRun.objects.all()), len(FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES) * 2)

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
