import random

from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data, get_random_string
from .models import *
from .transformers import ArchivesSpaceDataTransformer, CartographerDataTransformer


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


class TransformTest(TestCase):
    def setUp(self):
        self.client = Client()

    def import_endpoint(self):
        print("*** Testing import endpoint ***")
        response = self.client.post(reverse('import-data'))
        self.assertEqual(response.status_code, 200)

    def archivesspace_transform(self):
        print("*** Testing ArchivesSpace transforms ***")
        run_number = 1
        for object_type in ['agents', 'collections', 'objects', 'terms']:
            run = ArchivesSpaceDataTransformer(object_type).run()
            self.assertTrue(run)
            self.assertEqual(len(TransformRun.objects.all()), run_number)
            self.assertEqual(len(TransformRunError.objects.all()), 0)
            run_number += 1

    def cartographer_transform(self):
        print("*** Testing Cartographer transforms ***")
        run = CartographerDataTransformer().run()
        self.assertTrue(run)
        self.assertEqual(len(TransformRunError.objects.all()), 0)

    def transform_endpoint(self):
        print("*** Testing transform endpoint ***")
        for endpoint in ['transform-data']:
            response = self.client.post(reverse(endpoint))
            self.assertEqual(response.status_code, 200)

    def object_identifier_api(self):
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

    def generic_api_views(self):
        print("*** Testing API views ***")
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
        self.import_endpoint()
        self.archivesspace_transform()
        self.cartographer_transform()
        # self.transform_endpoint()
        self.object_identifier_api()
        self.generic_api_views()
        self.find_by_id()
