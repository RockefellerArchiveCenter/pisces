from django.urls import reverse
from rest_framework import serializers
from transformer.models import *


class DateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Date
        fields = ("begin", "end", "expression", "label")


class ExtentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extent
        fields = ('value', 'type')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('expression', 'identifier')


class SubnoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subnote
        fields = ("type", "content")


class NoteSerializer(serializers.ModelSerializer):
    content = SubnoteSerializer(source="subnote_set", many=True)

    class Meta:
        model = Note
        fields = ("type", "title", "content")


class RightsGrantedSerializer(serializers.ModelSerializer):
    note = NoteSerializer(source="note_set", many=True)

    class Meta:
        model = RightsGranted
        fields = ("act", "restriction", "dateStart", "dateEnd", "note")


class RightsStatementSerializer(serializers.ModelSerializer):
    rights_granted = RightsGrantedSerializer(source='rightsgranted_set', many=True)
    note = NoteSerializer(source="note_set", many=True)

    class Meta:
        model = RightsStatement
        fields = ("rightsType", "dateStart", "dateEnd", "determinationDate",
                  "rights_granted", "copyrightStatus", "otherBasis", "jurisdiction",
                  "note", "created", "modified")


class IdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identifier
        fields = ("source", "identifier", "created", "modified")


class SourceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceData
        fields = ('source', 'data')


class RelatedSerializer(serializers.Serializer):
    title = serializers.StringRelatedField()
    ref = serializers.SerializerMethodField()

    def get_ref(self, obj):
        print(self)
        return "test"


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    languages = LanguageSerializer(many=True)
    dates = DateSerializer(source="date_set", many=True)
    extents = ExtentSerializer(source="extent_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    rights_statements = RightsStatementSerializer(source="rightsstatement_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    source_data = SourceDataSerializer(source="sourcedata_set", many=True)
    collections = RelatedSerializer(source="collection_set", many=True, context={"view_name": 'collection-detail'})
    objects = serializers.HyperlinkedRelatedField(source="object_set", many=True, read_only=True, view_name='object-detail')

    class Meta:
        model = Collection
        fields = ("url", "title", "dates", "creators", "languages", "notes",
                  "extents", "level", "agents", "terms", "parent", "collections",
                  "objects", "rights_statements", "identifiers", "source_data",
                  "tree", "created", "modified", )


class CollectionListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Collection
        fields = ('url', 'title')


class ObjectSerializer(serializers.HyperlinkedModelSerializer):
    languages = LanguageSerializer(many=True)
    dates = DateSerializer(source="date_set", many=True)
    extents = ExtentSerializer(source="extent_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    rights_statements = RightsStatementSerializer(source="rightsstatement_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    source_data = SourceDataSerializer(source="sourcedata_set", many=True)

    class Meta:
        model = Object
        fields = ("url", "title", "dates", "languages", "notes", "extents",
                  "agents", "terms", "parent", "identifiers", "rights_statements",
                  "source_data", "created", "modified")


class ObjectListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Object
        fields = ('url', 'title')


class AgentSerializer(serializers.HyperlinkedModelSerializer):
    dates = DateSerializer(source="date_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    source_data = SourceDataSerializer(source="sourcedata_set", many=True)

    class Meta:
        model = Agent
        fields = ("url", "title", "dates", "type", "notes", "identifiers",
                  "source_data", "created", "modified")


class AgentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = ('url', 'title')


class TermSerializer(serializers.HyperlinkedModelSerializer):
    notes = NoteSerializer(source="note_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    source_data = SourceDataSerializer(source="sourcedata_set", many=True)

    class Meta:
        model = Term
        fields = ("url", "title", "type", "notes", "identifiers", "source_data",
                  "created", "modified")


class TermListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Term
        fields = ('url', 'title')
