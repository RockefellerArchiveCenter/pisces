from django.test import Client, TestCase
from django.urls import reverse

from .test_library import import_fixture_data
from .models import TransformRun, TransformRunError
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

    def test_transforms(self):
        self.import_endpoint()
        self.archivesspace_transform()
        self.cartographer_transform()
        self.transform_endpoint()
