from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .models import Collection, Object, Agent, Term
from .serializers import *


class CollectionViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a Collection, identified by a primary key.

    list:
    Return paginated data about all Collections.
    """
    model = Collection
    queryset = Collection.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionSerializer


class ObjectViewSet(ModelViewSet):
    """
    retrieve:
    Return data about an Object, identified by a primary key.

    list:
    Return paginated data about all Objects.
    """
    model = Object
    queryset = Object.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ObjectListSerializer
        return ObjectSerializer


class AgentViewSet(ModelViewSet):
    """
    retrieve:
    Return data about an Agent, identified by a primary key.

    list:
    Return paginated data about all Agents.
    """
    model = Agent
    queryset = Agent.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AgentListSerializer
        return AgentSerializer


class TermViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a Term, identified by a primary key.

    list:
    Return paginated data about all Terms.
    """
    model = Term
    queryset = Term.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return TermListSerializer
        return TermSerializer
