from django.db import models


class Identifier(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class ExternalIdentifier(models.Model):
    AURORA = 0
    ARCHIVEMATICA = 1
    FEDORA = 2
    ARCHIVESSPACE = 3
    DIMES = 4
    SOURCE_CHOICES = (
        (AURORA, 'Aurora'),
        (ARCHIVEMATICA, 'Archivematica'),
        (FEDORA, 'Fedora'),
        (ARCHIVESSPACE, 'ArchivesSpace'),
        (DIMES, 'DIMES')
    )
    source = models.CharField(max_length=256, choices=SOURCE_CHOICES)
    source_identifier = models.CharField(max_length=256, choices=SOURCE_CHOICES)
    identifier = models.ForeignKey(Identifier, on_delete=models.CASCADE, related_name='external_identifiers')
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
