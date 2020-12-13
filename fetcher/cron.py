from datetime import datetime

from django_cron import CronJobBase, Schedule

from .fetchers import ArchivesSpaceDataFetcher, CartographerDataFetcher
from .models import FetchRun


class BaseCron(CronJobBase):
    RUN_EVERY_MINS = 0
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        start = datetime.now()
        source = [s[1] for s in FetchRun.SOURCE_CHOICES if s[0] == self.fetcher.source][0]
        print("Export of {} {} records from {} started at {}".format(
            self.object_status, self.object_type, source, start))
        out = self.fetcher().fetch(self.object_status, self.object_type)
        end = datetime.now()
        fetch_run = FetchRun.objects.filter(
            status=FetchRun.FINISHED,
            source=self.fetcher.source,
            object_type=self.object_type,
            object_status=self.object_status).order_by("-end_time")[0]
        print("{} records exported in {}".format(out, end - start))
        if fetch_run.error_count:
            print("{} errors".format(fetch_run.error_count))
            for e in fetch_run.errors:
                print("    {}".format(e.message))
        print("Export of {} {} records from {} complete at {}\n".format(
            self.object_status, self.object_type, source, end))


class DeletedArchivesSpacePeople(BaseCron):
    code = "fetcher.deleted_archivesspace_people"
    object_status = "deleted"
    object_type = "agent_person"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpacePeople(BaseCron):
    code = "fetcher.updated_archivesspace_people"
    object_status = "updated"
    object_type = "agent_person"
    fetcher = ArchivesSpaceDataFetcher


class DeletedArchivesSpaceOrganizations(BaseCron):
    code = "fetcher.deleted_archivesspace_organizations"
    object_status = "deleted"
    object_type = "agent_corporate_entity"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceOrganizations(BaseCron):
    code = "fetcher.updated_archivesspace_organizations"
    object_status = "updated"
    object_type = "agent_corporate_entity"
    fetcher = ArchivesSpaceDataFetcher


class DeletedArchivesSpaceFamilies(BaseCron):
    code = "fetcher.deleted_archivesspace_families"
    object_status = "deleted"
    object_type = "agent_family"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceFamilies(BaseCron):
    code = "fetcher.updated_archivesspace_families"
    object_status = "updated"
    object_type = "agent_family"
    fetcher = ArchivesSpaceDataFetcher


class DeletedArchivesSpaceSubjects(BaseCron):
    code = "fetcher.deleted_archivesspace_subjects"
    object_status = "deleted"
    object_type = "subject"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceSubjects(BaseCron):
    code = "fetcher.updated_archivesspace_subjects"
    object_status = "updated"
    object_type = "subject"
    fetcher = ArchivesSpaceDataFetcher


class DeletedArchivesSpaceResources(BaseCron):
    code = "fetcher.deleted_archivesspace_resources"
    object_status = "deleted"
    object_type = "resource"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceResources(BaseCron):
    code = "fetcher.updated_archivesspace_resources"
    object_status = "updated"
    object_type = "resource"
    fetcher = ArchivesSpaceDataFetcher


class DeletedArchivesSpaceArchivalObjects(BaseCron):
    code = "fetcher.deleted_archivesspace_archival_objects"
    object_status = "deleted"
    object_type = "archival_object"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceArchivalObjects(BaseCron):
    code = "fetcher.updated_archivesspace_archival_objects"
    object_status = "updated"
    object_type = "archival_object"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedCartographerArrangementMapComponents(BaseCron):
    code = "fetcher.updated_cartographer_arrangement_map_components"
    object_status = "updated"
    object_type = "arrangement_map_component"
    fetcher = CartographerDataFetcher


class CleanUpCompleted(CronJobBase):
    code = "fetcher.cleanup_completed"
    RUN_EVERY_MINS = 0
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        try:
            for obj_type, _ in FetchRun.OBJECT_TYPE_CHOICES:
                delete_ids = FetchRun.objects.filter(
                    object_type=obj_type,
                    status=FetchRun.FINISHED,
                    fetchrunerror__isnull=True).order_by("-end_time")[1:].values_list("id", flat=True)
                FetchRun.objects.filter(pk__in=list(delete_ids)).delete()
                print("{} {} FetchRun objects deleted".format(len(delete_ids), obj_type))
        except Exception as e:
            print("Error cleaning  up completed FetchRun objects: {}".format(e))
            return False
