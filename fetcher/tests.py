import random
from datetime import datetime
from unittest.mock import patch

import pytz
import vcr
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from .cron import (CleanUpCompleted, DeletedArchivesSpaceArchivalObjects,
                   DeletedArchivesSpaceFamilies,
                   DeletedArchivesSpaceOrganizations,
                   DeletedArchivesSpacePeople, DeletedArchivesSpaceResources,
                   DeletedArchivesSpaceSubjects,
                   DeletedCartographerArrangementMapComponents,
                   UpdatedArchivesSpaceArchivalObjects,
                   UpdatedArchivesSpaceFamilies,
                   UpdatedArchivesSpaceOrganizations,
                   UpdatedArchivesSpacePeople, UpdatedArchivesSpaceResources,
                   UpdatedArchivesSpaceSubjects,
                   UpdatedCartographerArrangementMapComponents)
from .fetchers import ArchivesSpaceDataFetcher, CartographerDataFetcher
from .helpers import last_run_time, send_error_notification
from .models import FetchRun, FetchRunError
from .views import FetchRunViewSet

archivesspace_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/fetcher',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)

cartographer_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/fetcher',
    record_mode='once',
    match_on=['path', 'method'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
)


class FetcherTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        time = pytz.utc.localize(datetime(2020, 3, 1))
        for object_status, _ in FetchRun.OBJECT_STATUS_CHOICES:
            for _, source in FetchRun.SOURCE_CHOICES:
                for object_type, _ in getattr(FetchRun, "{}_OBJECT_TYPE_CHOICES".format(source.upper())):
                    f = FetchRun.objects.create(
                        status=FetchRun.FINISHED,
                        source=getattr(FetchRun, source.upper()),
                        object_type=object_type,
                        object_status=object_status
                    )
                    f.start_time = time
                    f.save()

    @patch("transformer.transformers.Transformer.run")
    @patch("merger.mergers.BaseMerger.merge")
    @patch("fetcher.helpers.identifier_from_uri")
    def test_fetchers(self, mock_id, mock_merger, mock_transformer):
        mock_id.return_value = None
        mock_merger.return_value = {}, {}
        mock_transformer.return_value = {}
        for object_type_choices, fetcher, fetcher_vcr, cassette_prefix in [
                (FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES, ArchivesSpaceDataFetcher, archivesspace_vcr, "ArchivesSpace"),
                (FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES, CartographerDataFetcher, cartographer_vcr, "Cartographer")]:
            for status in ["updated", "deleted"]:
                for object_type, _ in object_type_choices:
                    with fetcher_vcr.use_cassette("{}-{}-{}.json".format(cassette_prefix, status, object_type)):
                        processed = fetcher().fetch(status, object_type)
                        self.assertTrue(isinstance(processed, int))
            self.assertTrue(len(FetchRun.objects.all()), len(object_type_choices) * 2)

    def test_action_views(self):
        for action in ["archivesspace", "cartographer", "archival_objects",
                       "families", "organizations", "people", "resources",
                       "arrangement_map_components"]:
            view = FetchRunViewSet.as_view({"get": action})
            request = self.factory.get("fetchrun-list")
            response = view(request)
            self.assertEqual(
                response.status_code, 200,
                "View error:  {}".format(response.data))

    def test_last_run(self):
        for object_status, _ in FetchRun.OBJECT_STATUS_CHOICES:
            for _, source in FetchRun.SOURCE_CHOICES:
                for object in getattr(FetchRun, "{}_OBJECT_TYPE_CHOICES".format(source.upper())):
                    last_run = last_run_time(source, object_status, object)
                    self.assertEqual(last_run, 0)
                    time = timezone.now()
                    FetchRun.objects.create(
                        status=FetchRun.FINISHED,
                        source=source,
                        object_type=object,
                        object_status=object_status,
                        end_time=time)
                    updated_last_run = last_run_time(source, object_status, object)
                    self.assertEqual(updated_last_run, int(time.timestamp()))

    @patch("transformer.transformers.Transformer.run")
    @patch("merger.mergers.BaseMerger.merge")
    @patch("fetcher.helpers.identifier_from_uri")
    def test_cron(self, mock_id, mock_merger, mock_transformer):
        for fetcher_vcr, cassette, cron in [
                (archivesspace_vcr, "ArchivesSpace-deleted-agent_corporate_entity.json", DeletedArchivesSpaceOrganizations),
                (archivesspace_vcr, "ArchivesSpace-updated-agent_corporate_entity.json", UpdatedArchivesSpaceOrganizations),
                (archivesspace_vcr, "ArchivesSpace-deleted-agent_family.json", DeletedArchivesSpaceFamilies),
                (archivesspace_vcr, "ArchivesSpace-updated-agent_family.json", UpdatedArchivesSpaceFamilies),
                (archivesspace_vcr, "ArchivesSpace-deleted-agent_person.json", DeletedArchivesSpacePeople),
                (archivesspace_vcr, "ArchivesSpace-updated-agent_person.json", UpdatedArchivesSpacePeople),
                (archivesspace_vcr, "ArchivesSpace-deleted-subject.json", DeletedArchivesSpaceSubjects),
                (archivesspace_vcr, "ArchivesSpace-updated-subject.json", UpdatedArchivesSpaceSubjects),
                (archivesspace_vcr, "ArchivesSpace-deleted-resource.json", DeletedArchivesSpaceResources),
                (archivesspace_vcr, "ArchivesSpace-updated-resource.json", UpdatedArchivesSpaceResources),
                (archivesspace_vcr, "ArchivesSpace-deleted-archival_object.json", DeletedArchivesSpaceArchivalObjects),
                (archivesspace_vcr, "ArchivesSpace-updated-archival_object.json", UpdatedArchivesSpaceArchivalObjects),
                (cartographer_vcr, "Cartographer-deleted-arrangement_map_component.json", DeletedCartographerArrangementMapComponents),
                (cartographer_vcr, "Cartographer-updated-arrangement_map_component.json", UpdatedCartographerArrangementMapComponents)]:
            with fetcher_vcr.use_cassette(cassette):
                mock_id.return_value = None
                mock_merger.return_value = {}, {}
                mock_transformer.return_value = {}
                cron().do()
                self.assertEqual(len(FetchRunError.objects.all()), 0)

    def test_error_notifications(self):
        fetch_run = FetchRun.objects.create(
            object_type=random.choice(FetchRun.OBJECT_TYPE_CHOICES)[0],
            source=random.choice(FetchRun.SOURCE_CHOICES)[0],
            status=random.choice(FetchRun.STATUS_CHOICES)[0],
            object_status=random.choice(FetchRun.OBJECT_STATUS_CHOICES)[0])
        error = FetchRunError.objects.create(message="This is an error!", run=fetch_run)
        send_error_notification(fetch_run)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(fetch_run.get_object_type_display(), mail.outbox[0].subject)
        source = [s[1] for s in FetchRun.SOURCE_CHOICES if s[0] == int(fetch_run.source)][0]
        self.assertIn(source, mail.outbox[0].subject)
        self.assertNotIn("errors", mail.outbox[0].subject)
        self.assertIn(error.message, mail.outbox[0].body)

    def test_cleanup(self):
        for source_id, source in FetchRun.SOURCE_CHOICES:
            for object in getattr(FetchRun, "{}_OBJECT_TYPE_CHOICES".format(source.upper())):
                last_run = last_run_time(source, FetchRun.FINISHED, object)
                cleanup = CleanUpCompleted().do()
                self.assertIsNot(False, cleanup)
                self.assertEqual(last_run, last_run_time(source, FetchRun.FINISHED, object))
                self.assertEqual(
                    len(FetchRun.objects.filter(source=source_id, object_type=object[0], status=FetchRun.FINISHED)), 2)
