from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class FetchRun(models.Model):
    STARTED = 0
    FINISHED = 1
    ERRORED = 2
    STATUS_CHOICES = (
        (STARTED, 'Started'),
        (FINISHED, 'Finished'),
        (ERRORED, 'Errored'),
    )
    ARCHIVESSPACE = 0
    CARTOGRAPHER = 1
    SOURCE_CHOICES = (
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (CARTOGRAPHER, 'Cartographer'),
    )
    ARCHIVESSPACE_OBJECT_TYPE_CHOICES = (
        ('resource', 'Resource'),
        ('archival_object', 'Archival Object'),
        ('subject', 'Subject'),
        ('agent_person', 'Person'),
        ('agent_corporate_entity', 'Organization'),
        ('agent_family', 'Family'),
    )
    CARTOGRAPHER_OBJECT_TYPE_CHOICES = (
        ('arrangement_map_component', 'Arrangement Map Component'),
    )
    OBJECT_TYPE_CHOICES = ARCHIVESSPACE_OBJECT_TYPE_CHOICES + CARTOGRAPHER_OBJECT_TYPE_CHOICES
    OBJECT_STATUS_CHOICES = (("updated", "Updated"), ("deleted", "Deleted"))
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES)
    object_status = models.CharField(max_length=100, choices=OBJECT_STATUS_CHOICES)

    @property
    def errors(self):
        return FetchRunError.objects.filter(run=self)

    @property
    def error_count(self):
        return len(FetchRunError.objects.filter(run=self))

    @property
    def elapsed(self):
        if (self.end_time and self.end_time):
            return self.end_time - self.start_time
        return 0


class FetchRunError(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    message = models.TextField(max_length=255)
    run = models.ForeignKey(FetchRun, on_delete=models.CASCADE)

    class Meta:
        ordering = ('datetime', )
