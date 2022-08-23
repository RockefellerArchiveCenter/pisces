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
    data = models.JSONField()
    indexed = models.BooleanField(default=False)
    online_pending = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class ConfigurationList(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class ConfigurationChoice(models.Model):
    list = models.ForeignKey(ConfigurationList, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return self.value
