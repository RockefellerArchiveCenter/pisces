from django.test import TestCase

from .test_library import import_fixture_data
from .models import TransformRun, TransformRunError
from .transformers import ArchivesSpaceDataTransformer, CartographerDataTransformer


class TransformTest(TestCase):
    def setUp(self):
        import_fixture_data()

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

    def test_transforms(self):
        self.archivesspace_transform()
        self.cartographer_transform()
