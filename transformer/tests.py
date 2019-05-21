import random

from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data, get_random_string
from .models import *
from .transformers import ArchivesSpaceDataTransformer, CartographerDataTransformer


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
        for endpoint in ['transform-data', 'import-data']:
            response = self.client.post(reverse(endpoint))
            self.assertEqual(response.status_code, 200)

    def object_identifier_api(self):
        print("*** Testing custom identifier endpoints ***")
        OBJECT_MAP = [
            (Collection, 'collection'),
            (Object, 'object'),
            (Term, 'term'),
            (Agent, 'agent')
        ]
        for obj in OBJECT_MAP:
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
            self.assertEqual(delete.status_code, 201, "Wrong HTTP status returned, should be 201")
            self.assertEqual(len(Identifier.objects.filter(**{obj[1]: o})), len(assigned_ids), "An identifier was not deleted.")
            self.assertEqual(len(Note.objects.filter(**{obj[1]: o, "source": getattr(Note, s.upper())})), 0, "Notes from identifier's source were not deleted")

    def test_transforms(self):
        self.import_endpoint()
        self.archivesspace_transform()
        self.cartographer_transform()
        self.transform_endpoint()
        self.object_identifier_api()
