import json
import vcr

from django.test import TestCase

from .fetchers import ArchivesSpaceDataFetcher
from .models import FetchRun

fetch_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)


class FetcherTest(TestCase):

    def test_archivesspace(self):
        for meth in ["get_updated", "get_deleted"]:
            with fetch_vcr.use_cassette("ArchivesSpace-{}.json".format(resource[0])) as cass:
                for i, object_type in enumerate(FetchRun.OBJECT_TYPE_CHOICES):
                    list = getattr(ArchivesSpaceDataFetcher, meth)(object_type)
                    self.assertEqual(len(FetchRun.objects.all()), i + 1)
                    if meth == "get_updated":
                        for obj in list:
                            self.assertTrue(isinstance(obj, dict))
                            self.assertTrue(obj.get('publish'))
                    else:
                        for obj in list:
                            self.assertTrue(isinstance(obj, str))
