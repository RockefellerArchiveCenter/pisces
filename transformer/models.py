from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from silk.profiling.profiler import silk_profile


class DataObject(models.Model):
    TYPE_CHOICES = (
        ('agent', 'Agent'),
        ('collection', 'Collection'),
        ('object', 'Object'),
        ('term', 'Term'),
    )
    es_id = models.CharField(max_length=255)
    object_type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    data = JSONField()
    indexed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(
                fields=['data'],
                name='data_gin',
            ),
        ]

    @classmethod
    @silk_profile()
    def find_matches(self, object_type, source, identifier):
        return DataObject.objects.filter(
            object_type=object_type,
            data__external_identifiers__contains=[
                {"source": source, "identifier": identifier}
            ])
