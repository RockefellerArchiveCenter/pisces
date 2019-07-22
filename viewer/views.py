from django.views.generic import TemplateView
from rest_framework.views import APIView

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Search

from transformer.documents import Collection, Object, Agent, Term
from .helpers import document_or_404, documents_of_type

from pisces import config


class SearchView(APIView):
    def __init__(self):
        connections.create_connection(hosts=['elasticsearch'], timeout=20)


class CollectionListView(SearchView):
    def get(self, request, *args, **kwargs):
        return documents_of_type(Collection, 'collection')


class CollectionDetailView(SearchView):
    def get(self, request, *args, **kwargs):
        return document_or_404(Collection, kwargs.get('id'))


class ObjectListView(SearchView):
    def get(self, request, *args, **kwargs):
        return documents_of_type(Object, 'object')


class ObjectDetailView(SearchView):
    def get(self, request, *args, **kwargs):
        return document_or_404(Object, kwargs.get('id'))


class AgentListView(SearchView):
    def get(self, request, *args, **kwargs):
        return documents_of_type(Agent, 'agent')


class AgentDetailView(SearchView):
    def get(self, request, *args, **kwargs):
        return document_or_404(Agent, kwargs.get('id'))


class TermListView(SearchView):
    def get(self, request, *args, **kwargs):
        return documents_of_type(Term, 'term')


class TermDetailView(SearchView):
    def get(self, request, *args, **kwargs):
        return document_or_404(Term, kwargs.get('id'))


class IndexView(TemplateView):
    template_name = 'viewer/index.html'
