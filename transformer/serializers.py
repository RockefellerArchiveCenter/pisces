from rest_framework import serializers
from transformer.models import Collection, Object, Agent, Term


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'


class CollectionListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Collection
        fields = ('url', 'title')


class ObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Object
        fields = '__all__'


class ObjectListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Object
        fields = ('url', 'title')


class AgentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'


class AgentListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = ('url', 'title')


class TermSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Term
        fields = '__all__'


class TermListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Term
        fields = ('url', 'title')
