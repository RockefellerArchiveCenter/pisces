from django.test import TestCase

from .test_library import import_fixture_data
from .models import TransformRun, TransformRunError
from .transformers import ArchivesSpaceDataTransformer, ArrangementMapDataTransformer, TreeOrderTransformer


class TransformTest(TestCase):
    def setUp(self):
        import_fixture_data()

    def test_transform(self):
        print("*** Testing transforms ***")
        run_number = 1
        for transformer in [ArchivesSpaceDataTransformer, ArrangementMapDataTransformer, TreeOrderTransformer]:
            run = transformer().run()
            self.assertTrue(run)
            self.assertEqual(len(TransformRun.objects.all()), run_number)
            self.assertEqual(len(TransformRunError.objects.all()), 0)
            run_number += 1
