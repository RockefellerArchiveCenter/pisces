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
    def to_representation(self, obj):
        return {
            "title": obj.title,
            "ref": reverse("{}-detail".format(obj.__class__.__name__.lower()), kwargs={"pk": obj.pk})
        }


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    languages = LanguageSerializer(many=True)
    dates = DateSerializer(source="date_set", many=True)
    extents = ExtentSerializer(source="extent_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    rights_statements = RightsStatementSerializer(source="rightsstatement_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    collections = RelatedSerializer(source="collection_set", many=True)
    objects = RelatedSerializer(source="object_set", many=True)
    terms = RelatedSerializer(many=True)
    agents = RelatedSerializer(many=True)
    creators = RelatedSerializer(many=True)
    parent = RelatedSerializer()

    class Meta:
        model = Collection
        fields = ("url", "title", "dates", "creators", "languages", "notes",
                  "extents", "level", "agents", "terms", "parent", "collections",
                  "objects", "rights_statements", "identifiers", "tree", "created",
                  "modified", )


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
    terms = RelatedSerializer(many=True)
    agents = RelatedSerializer(many=True)
    parent = RelatedSerializer()

    class Meta:
        model = Object
        fields = ("url", "title", "dates", "languages", "notes", "extents",
                  "agents", "terms", "parent", "identifiers", "rights_statements",
                  "created", "modified")


class ObjectListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Object
        fields = ('url', 'title')


class AgentSerializer(serializers.HyperlinkedModelSerializer):
    dates = DateSerializer(source="date_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)

    class Meta:
        model = Agent
        fields = ("url", "title", "dates", "type", "notes", "identifiers",
                  "created", "modified")


class AgentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = ('url', 'title')


class TermSerializer(serializers.HyperlinkedModelSerializer):
    notes = NoteSerializer(source="note_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)

    class Meta:
        model = Term
        fields = ("url", "title", "type", "notes", "identifiers", "created", "modified")


class TermListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Term
        fields = ('url', 'title')
