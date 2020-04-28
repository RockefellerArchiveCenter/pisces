from django_cron import CronJobBase, Schedule

from .fetchers import ArchivesSpaceDataFetcher
from .models import FetchRun


class BaseCron(CronJobBase):
    RUN_EVERY_MINS = 0
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        source = [s[1] for s in FetchRun.SOURCE_CHOICES if s[0] == self.fetcher.source][0]
        print("Export of {} {} records from {} started".format(self.object_status, self.object_type, source))
        try:
            out = self.fetcher().fetch(self.object_status, self.object_type)
            fetch_run = FetchRun.objects.filter(
                status=FetchRun.FINISHED,
                source=self.fetcher.source,
                object_type=self.object_type,
                object_status=self.object_status).order_by("-end_time")[0]
        except Exception as e:
            print(e)
        print("{} records exported".format(len(out)))
        if fetch_run.error_count:
            print("{} errors".format(fetch_run.error_count))
            for e in fetch_run.errors:
                print("    {}".format(e.message))
        print("Export of {} {} from {} complete".format(self.object_status, self.object_type, source))


class UpdatedArchivesSpacePeople(BaseCron):
    code = "fetcher.updated_archivesspace_people"
    object_status = "updated"
    object_type = "agent_person"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceOrganizations(BaseCron):
    code = "fetcher.updated_archivesspace_organizations"
    object_status = "updated"
    object_type = "agent_corporate_entity"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceFamilies(BaseCron):
    code = "fetcher.updated_archivesspace_families"
    object_status = "updated"
    object_type = "agent_family"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceSubjects(BaseCron):
    code = "fetcher.updated_archivesspace_subjects"
    object_status = "updated"
    object_type = "subject"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceResources(BaseCron):
    code = "fetcher.updated_archivesspace_resources"
    object_status = "updated"
    object_type = "resource"
    fetcher = ArchivesSpaceDataFetcher


class UpdatedArchivesSpaceArchivalObjects(BaseCron):
    code = "fetcher.updated_archivesspace_archival_objects"
    object_status = "updated"
    object_type = "archival_object"
    fetcher = ArchivesSpaceDataFetcher
