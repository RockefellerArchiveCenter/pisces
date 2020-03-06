from rest_framework import serializers

from .models import DataObject


class DataObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataObject
        fields = '__all__'


class DataObjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataObject
        fields = ('id', 'es_id', 'object_type')
