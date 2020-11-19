from django.contrib.postgres.fields import JSONField
from django.db import models


class DataObject(models.Model):
    TYPE_CHOICES = (
        ('agent', 'Agent'),
        ('collection', 'Collection'),
        ('object', 'Object'),
        ('term', 'Term'),
    )
    es_id = models.CharField(primary_key=True, max_length=255)
    object_type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    data = JSONField()
    indexed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
