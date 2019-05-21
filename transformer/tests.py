import vcr

from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data, add_wikidata_ids, add_wikipedia_ids
from .models import TransformRun, TransformRunError
from .fetchers import *
from .transformers import *

fetch_vcr = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='fixtures/cassettes',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)


class TransformTest(TestCase):
    def setUp(self):
        self.client = Client()
        import_fixture_data()

    def fetchers(self):
        FETCHER_MAP = [
            (ArchivesSpaceDataFetcher, 'archivesspace_fetch.yml', 'ARCHIVESSPACE'),
            (CartographerDataFetcher, 'cartographer_fetch.yml', 'CARTOGRAPHER'),
            (WikidataDataFetcher, 'wikidata_fetch.yml', 'WIKIDATA'),
            (WikipediaDataFetcher, 'wikipedia_fetch.yml', 'WIKIPEDIA'),
        ]
        for fetcher in FETCHER_MAP:
            if fetcher[2] == 'WIKIDATA': add_wikidata_ids()
            if fetcher[2] == 'WIKIPEDIA': add_wikipedia_ids()
            fetch_source = getattr(FetchRun, fetcher[2])
            source_source = getattr(SourceData, fetcher[2])
            identifier_source = getattr(Identifier, fetcher[2])
            with fetch_vcr.use_cassette(fetcher[1]):
                run = fetcher[0]().run()
            self.assertTrue(run)
            self.assertEqual(len(FetchRun.objects.filter(source=fetch_source)), 1)
            fetch_obj = FetchRun.objects.get(source=fetch_source)
            self.assertEqual(int(fetch_obj.status), FetchRun.FINISHED)
            self.assertEqual(len(FetchRunError.objects.filter(run=run)), 0)
            self.assertTrue(len(SourceData.objects.filter(source=source_source)) > 0)
            self.assertTrue(len(Identifier.objects.filter(source=identifier_source)) > 0)

    def transformers(self):
        TRANSFORMER_MAP = [
            (ArchivesSpaceDataTransformer, 'ARCHIVESSPACE'),
            (CartographerDataTransformer, 'CARTOGRAPHER'),
            (WikidataDataTransformer, 'WIKIDATA'),
            (WikipediaDataTransformer, 'WIKIPEDIA'),
        ]
        for transformer in TRANSFORMER_MAP:
            transform_source = getattr(TransformRun, transformer[1])
            id_source = getattr(Identifier, transformer[1])
            run = transformer[0]().run()
            self.assertTrue(run)
            self.assertEqual(len(TransformRun.objects.filter(source=transform_source)), 1)
            transform_obj = TransformRun.objects.get(source=transform_source)
            self.assertEqual(int(transform_obj.status), TransformRun.FINISHED)
            self.assertEqual(len(TransformRunError.objects.filter(run=run)), 0)

    def transform_endpoint(self):
        print("*** Testing transform endpoint ***")
        response = self.client.post(reverse('transform-data'))
        self.assertEqual(response.status_code, 200)

    def test_transforms(self):
        self.fetchers()
        self.transformers()
        self.transform_endpoint()
