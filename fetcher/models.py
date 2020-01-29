from django.db import models
from django.contrib.auth.models import AbstractUser


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
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    PISCES = 4
    CARTOGRAPHER = 5
    TREES = 6
    WIKIDATA = 7
    WIKIPEDIA = 8
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (PISCES, 'Pisces'),
        (CARTOGRAPHER, 'Cartographer'),
        (TREES, 'Trees'),
        (WIKIDATA, 'Wikidata'),
        (WIKIPEDIA, 'Wikipedia')
    )
    OBJECT_TYPE_CHOICES = (
        ('agents', 'Agents'),
        ('resources', 'Resources'),
        ('objects', 'Objects'),
        ('terms', 'Terms')
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES, null=True, blank=True)


class FetchRunError(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    run = models.ForeignKey(FetchRun, on_delete=models.CASCADE)
