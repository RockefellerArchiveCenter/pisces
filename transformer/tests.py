from django.test import TestCase

from .library import import_fixture_data
from .models import TransformRun, TransformRunError
from .transformers import ArchivesSpaceDataTransformer, ArrangementMapDataTransformer


class TransformTest(TestCase):
    def setUp(self):
        import_fixture_data()

    def test_transform(self):
        run_number = 1
        for transformer in [ArchivesSpaceDataTransformer, ArrangementMapDataTransformer]:
            run = getattr(transformer(), 'run')()
            self.assertTrue(run)
            self.assertEqual(len(TransformRun.objects.all()), run_number)
            self.assertEqual(len(TransformRunError.objects.all()), 0)
            run_number += 1
