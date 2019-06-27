from itertools import chain

from django.urls import reverse
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from transformer.models import *


class FetchRunErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FetchRunError
        fields = ('datetime', 'message')


class FetchRunSerializer(serializers.HyperlinkedModelSerializer):
    errors = FetchRunErrorSerializer(source='fetchrunerror_set', many=True)
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = FetchRun
        fields = ('url', 'status', 'source', 'object_type', 'errors', 'start_time', 'end_time')

    def get_source(self, obj):
        return obj.SOURCE_CHOICES[int(obj.source)][1]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]


class FetchRunListSerializer(serializers.HyperlinkedModelSerializer):
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = FetchRun
        fields = ('url', 'status', 'source', 'object_type')

    def get_source(self, obj):
        return obj.SOURCE_CHOICES[int(obj.source)][1]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]
