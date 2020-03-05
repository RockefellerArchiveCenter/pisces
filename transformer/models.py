from django.contrib.postgres.fields import JSONField
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

    @classmethod
    @silk_profile()
    def find_matches(self, source, identifier, initial_queryset=None):
        matches = []
        initial_queryset = initial_queryset if initial_queryset else self.objects.all()
        for obj in initial_queryset:
            for id_obj in obj.data['external_identifiers']:
                if (id_obj['source'] == source and id_obj['identifier'] == identifier):
                    matches.append(obj)
        return matches
