from django.test import TestCase

from .models import TransformRun
from .transformers import ArchivesSpaceDataTransformer


class TransformTest(TestCase):
    # def setUp(self):
        # create objects in database

    def test_transform(self):
        run = ArchivesSpaceDataTransformer().run()
        self.assertTrue(run)
        self.assertEqual(len(TransformRun.objects.all()), 1)
