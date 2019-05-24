import random
import vcr

from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data, add_wikidata_ids, add_wikipedia_ids, get_random_string
from .models import *
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
        print("*** Testing data fetchers ***")
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
        print("*** Testing data transformer ***")
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

    def api(self):
        # (Class, prefix, has identifier endpoints)
        OBJECT_MAP = [
            (Collection, 'collection', True),
            (Object, 'object', True),
            (Term, 'term', True),
            (Agent, 'agent', True),
            (Identifier, 'identifier', False),
            (TransformRun, 'transformrun', False),
            (FetchRun, 'fetchrun', False)
        ]
        print("*** Testing transform endpoint ***")
        response = self.client.post(reverse('transform-data'))
        self.assertEqual(response.status_code, 200)

        print("*** Testing custom identifier endpoints ***")
        for obj in OBJECT_MAP:
            if obj[2]:
                o = random.choice(obj[0].objects.all())
                view = '{}-identifiers'.format(obj[1])
                list = self.client.get(reverse(view, kwargs={"pk": o.pk}))
                self.assertEqual(list.status_code, 200, "Wrong HTTP status returned, should be 200")

                assigned_ids = [i['source'].lower() for i in list.json()]
                unassigned_ids = [i for i in ['archivesspace', 'cartographer', 'wikidata', 'wikipedia'] if i not in assigned_ids]
                s = random.choice(unassigned_ids)
                post = self.client.post("{}?source={}&identifier={}".format(reverse(view, kwargs={"pk": o.pk}), s, get_random_string()))
                self.assertEqual(post.status_code, 201, "Wrong HTTP status returned, should be 201")
                self.assertEqual(len(Identifier.objects.filter(**{obj[1]: o})), len(assigned_ids)+1, "An identifier was not created.")

                delete = self.client.delete("{}?source={}".format(reverse(view, kwargs={"pk": o.pk}), s))
                self.assertEqual(delete.status_code, 200, "Wrong HTTP status returned, should be 200")
                self.assertEqual(len(Identifier.objects.filter(**{obj[1]: o})), len(assigned_ids), "An identifier was not deleted.")
                self.assertEqual(len(Note.objects.filter(**{obj[1]: o, "source": getattr(Note, s.upper())})), 0, "Notes from identifier's source were not deleted")

        print("*** Testing generic API views ***")
        for obj in OBJECT_MAP:
            list = self.client.get(reverse("{}-list".format(obj[1])))
            self.assertEqual(list.status_code, 200, "Wrong HTTP status returned, should be 200")
            if len(obj[0].objects.all()):
                o = random.choice(obj[0].objects.all())
                detail = self.client.get(reverse("{}-detail".format(obj[1]), kwargs={"pk": o.pk}))
                self.assertEqual(detail.status_code, 200, "Wrong HTTP status returned, should be 200")

    def find_by_id(self):
        print("*** Testing Find By ID view ***")
        ident = random.choice(Identifier.objects.all())
        source = [i[1].lower() for i in Identifier.SOURCE_CHOICES if i[0] == int(ident.source)][0]
        find = self.client.get("{}?source={}&identifier={}".format(reverse('find-by-id'), source, ident.identifier))
        self.assertEqual(find.status_code, 200, "Wrong HTTP status returned, should be 200")
        self.assertEqual(find.json()['count'], 1, "Wrong number of objects returned")

    def test_transforms(self):
        self.transformers()
        self.fetchers()
        self.api()
        self.find_by_id()
