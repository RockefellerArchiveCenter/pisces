from itertools import chain

from django.urls import reverse
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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


class IdentifierSerializer(serializers.HyperlinkedModelSerializer):
    source = serializers.SerializerMethodField()

    class Meta:
        model = Identifier
        fields = ("url", "source", "identifier", "created", "modified")

    def get_source(self, obj):
        return [o[1] for o in obj.SOURCE_CHOICES if o[0] == int(obj.source)][0]


class RelatedSerializer(serializers.Serializer):
    def to_representation(self, obj):
        return {
            'title': obj.title,
            'ref': reverse('{}-detail'.format(obj.__class__.__name__.lower()), kwargs={'pk': obj.pk})
        }


class AncestorSerializer(serializers.Serializer):
    def to_representation(self, obj):
        view_name = "{}-detail".format(obj.__class__.__name__.lower())
        if obj.parent:
            self.ancestors = {'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk}), 'parent': []}
            self.process_ancestor_item(obj.parent, self.ancestors['parent'])
            return self.ancestors
        else:
            return {'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk})}

    def process_ancestor_item(self, obj, ancestors):
        view_name = "{}-detail".format(obj.__class__.__name__.lower())
        if obj.parent:
            ancestors.append({'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk}), 'parent': []})
            self.process_ancestor_item(obj.parent, ancestors[-1].get('parent'))
        else:
            ancestors.append({'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk})})
        return ancestors


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    languages = LanguageSerializer(many=True)
    dates = DateSerializer(source="date_set", many=True)
    extents = ExtentSerializer(source="extent_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    rights_statements = RightsStatementSerializer(source="rightsstatement_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    terms = RelatedSerializer(many=True)
    agents = RelatedSerializer(many=True)
    creators = RelatedSerializer(many=True)
    tree = serializers.SerializerMethodField()
    ancestors = AncestorSerializer(source="parent")

    class Meta:
        model = Collection
        fields = ("url", "title", "tree_order", "dates", "creators", "languages", "notes",
                  "extents", "level", "agents", "terms", "rights_statements",
                  "identifiers", "ancestors", "tree", "created", "modified",)

    def get_tree(self, obj):
        view_name = "{}-detail".format(obj.__class__.__name__.lower())
        if len(obj.collection_set.all() or obj.object_set.all()):
            self.tree = {'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk}), 'tree_order': obj.tree_order, 'children': []}
            self.process_tree_item(chain(obj.collection_set.all().order_by('tree_order'), obj.object_set.all().order_by('tree_order')), self.tree['children'])
            return self.tree
        else:
            return {'title': obj.title, 'ref': reverse(view_name, kwargs={"pk": obj.pk})}

    def process_tree_item(self, objects, tree):
        for item in objects:
            view_name = "{}-detail".format(item.__class__.__name__.lower())
            if isinstance(item, Collection) and len(item.collection_set.all() or item.object_set.all()):
                tree.append({'title': item.title, 'ref': reverse(view_name, kwargs={"pk": item.pk}), 'tree_order': item.tree_order, 'children': []})
                self.process_tree_item(chain(item.collection_set.all().order_by('tree_order'), item.object_set.all().order_by('tree_order')), tree[-1].get('children'))
            else:
                tree.append({'title': item.title, 'ref': reverse(view_name, kwargs={"pk": item.pk}), 'tree_order': item.tree_order})
        return tree


class CollectionListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Collection
        fields = ('url', 'title',)


class ObjectSerializer(serializers.HyperlinkedModelSerializer):
    languages = LanguageSerializer(many=True)
    dates = DateSerializer(source="date_set", many=True)
    extents = ExtentSerializer(source="extent_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    rights_statements = RightsStatementSerializer(source="rightsstatement_set", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)
    terms = RelatedSerializer(many=True)
    agents = RelatedSerializer(many=True)
    ancestors = AncestorSerializer(source="parent")

    class Meta:
        model = Object
        fields = ("url", "title", "tree_order", "dates", "languages", "notes", "extents",
                  "agents", "terms", "ancestors", "identifiers", "rights_statements",
                  "created", "modified")


class ObjectListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Object
        fields = ('url', 'title')


class AgentSerializer(serializers.HyperlinkedModelSerializer):
    dates = DateSerializer(source="date_set", many=True)
    notes = NoteSerializer(source="note_set", many=True)
    objects = RelatedSerializer(source="agent_objects", many=True)
    collections = serializers.SerializerMethodField()
    identifiers = IdentifierSerializer(source="identifier_set", many=True)

    class Meta:
        model = Agent
        fields = ("url", "title", "dates", "type", "notes", "objects", "collections", "identifiers",
                  "created", "modified")

    def get_collections(self, obj):
        queryset = set(Collection.objects.filter(agents=obj) | Collection.objects.filter(creators=obj))
        return RelatedSerializer(queryset, many=True).data


class AgentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = ('url', 'title')


class TermSerializer(serializers.HyperlinkedModelSerializer):
    notes = NoteSerializer(source="note_set", many=True)
    objects = RelatedSerializer(source="term_objects", many=True)
    collections = RelatedSerializer(source="term_collections", many=True)
    identifiers = IdentifierSerializer(source="identifier_set", many=True)

    class Meta:
        model = Term
        fields = ("url", "title", "type", "notes", "objects", "collections", "identifiers", "created", "modified")


class TermListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Term
        fields = ('url', 'title')


class TransformRunErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransformRunError
        fields = ('datetime', 'message')


class FetchRunErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FetchRunError
        fields = ('datetime', 'message')


class TransformRunSerializer(serializers.HyperlinkedModelSerializer):
    errors = TransformRunErrorSerializer(source='transformrunerror_set', many=True)
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = TransformRun
        fields = ('url', 'status', 'source', 'object_type', 'errors', 'start_time', 'end_time')

    def get_source(self, obj):
        return [o[1] for o in obj.SOURCE_CHOICES if o[0] == int(obj.source)][0]

    def get_status(self, obj):
        return [o[1] for o in obj.STATUS_CHOICES if o[0] == int(obj.source)][0]


class TransformRunListSerializer(serializers.HyperlinkedModelSerializer):
    source = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = TransformRun
        fields = ('url', 'status', 'source', 'object_type')

    def get_source(self, obj):
        return [o[1] for o in obj.SOURCE_CHOICES if o[0] == int(obj.source)][0]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]


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
        model = TransformRun
        fields = ('url', 'status', 'source', 'object_type')

    def get_source(self, obj):
        return obj.SOURCE_CHOICES[int(obj.source)][1]

    def get_status(self, obj):
        return obj.STATUS_CHOICES[int(obj.status)][1]
