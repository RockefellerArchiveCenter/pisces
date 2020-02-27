from rest_framework import serializers

from .models import FetchRun, FetchRunError


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
        fields = ('url', 'status', 'source', 'object_type', 'error_count', 'errors', 'start_time', 'end_time')

    def get_source(self, obj):
        return obj.SOURCE_CHOICES[int(obj.source)][1]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]


class FetchRunListSerializer(serializers.HyperlinkedModelSerializer):
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = FetchRun
        fields = ('url', 'status', 'source', 'object_type', 'error_count')

    def get_source(self, obj):
        return obj.SOURCE_CHOICES[int(obj.source)][1]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]
