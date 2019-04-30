from django.views.generic import DetailView, ListView, TemplateView

from transformer.models import Agent, Collection, Object, Term


class CollectionListView(ListView):
    model = Collection
    queryset = Collection.objects.filter(parent__isnull=True).order_by('title')
    template_name = 'viewer/collection_list.html'


class CollectionDetailView(DetailView):
    model = Collection
    template_name = 'viewer/collection_detail.html'


class ObjectDetailView(DetailView):
    model = Object
    template_name = 'viewer/object_detail.html'


class AgentListView(ListView):
    model = Agent
    queryset = Agent.objects.all().order_by('title')
    template_name = 'viewer/agent_list.html'


class AgentDetailView(DetailView):
    model = Agent
    template_name = 'viewer/agent_detail.html'


class TermListView(ListView):
    model = Term
    queryset = Term.objects.all().order_by('title')
    template_name = 'viewer/term_list.html'


class TermDetailView(DetailView):
    model = Term
    template_name = 'viewer/term_detail.html'


class IndexView(TemplateView):
    template_name = 'viewer/index.html'


class TreeView(DetailView):
    model = Collection
    template_name = 'viewer/collection-tree.html'
