from rest_framework import serializers
from .models import Identifier, ExternalIdentifier


class ExternalIdentifierSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExternalIdentifier
        fields = ('source', 'source_identifier', 'created', 'last_modified')


class IdentifierSerializer(serializers.HyperlinkedModelSerializer):
    external_identifiers = ExternalIdentifierSerializer(many=True)

    class Meta:
        model = Identifier
        fields = ('url', 'external_identifiers', 'created', 'last_modified')


class IdentifierListSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Identifier
        fields = ('url',)
