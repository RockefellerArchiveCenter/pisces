from django.http import JsonResponse
from django.views.generic import DetailView, ListView, TemplateView

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Search

from pisces import config


class CollectionListView(ListView):
    def __init__(self):
        self.client = Elasticsearch([config.ELASTICSEARCH['host']])

    def get(self, request, *args, **kwargs):
        s = Search(index='collection', using=self.client)\
            .query('match_all')
        resp = s.execute()
        data = []
        for hit in resp:
            data.append({'title': hit.title, 'id': hit.meta.id, 'doc_type': hit.meta.doc_type})
        return JsonResponse({'collections': data})


class CollectionDetailView(DetailView):
    def __init__(self):
        self.client = Elasticsearch([config.ELASTICSEARCH['host']])

    def get(self, request, *args, **kwargs):
        identifier = kwargs.get('id')
        print(identifier)
        s = Search(index='collection', using=self.client)\
            .query('match', _id=identifier)
        resp = s.execute()
        if resp.hits.total == 1:
            return JsonResponse({'title': resp.hits[0].title, 'id': resp.hits[0].meta.id, 'doc_type': resp.hits[0].meta.doc_type})
        return JsonResponse({"detail": "Wrong number of hits. Got {}, expected 1".format(resp.hits.total)}, status_code=500)


class ObjectDetailView(DetailView): pass


class AgentListView(ListView): pass


class AgentDetailView(DetailView): pass


class TermListView(ListView): pass


class TermDetailView(DetailView): pass


class IndexView(TemplateView):
    template_name = 'viewer/index.html'


class TreeView(DetailView): pass
