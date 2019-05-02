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
    template_name = 'viewer/agent_list.html'

    def get_context_data(self, **kwargs):
        context = super(AgentListView, self).get_context_data(**kwargs)
        context['data'] = {}
        for agent_type in ['agent_person', 'agent_corporate_entity', 'agent_family']:
            context[agent_type] = Agent.objects.filter(type=agent_type).order_by('title')
        return context


class AgentDetailView(DetailView):
    model = Agent
    template_name = 'viewer/agent_detail.html'


class TermListView(ListView):
    model = Term
    template_name = 'viewer/term_list.html'

    def get_context_data(self, **kwargs):
        context = super(TermListView, self).get_context_data(**kwargs)
        context['data'] = {}
        for term_type in ['cultural_context', 'function', 'geographic',
                          'genre_form', 'occupation', 'style_period',
                          'technique', 'temporal', 'topical']:
            context[term_type] = Term.objects.filter(type=term_type).order_by('title')
        return context


class TermDetailView(DetailView):
    model = Term
    template_name = 'viewer/term_detail.html'


class IndexView(TemplateView):
    template_name = 'viewer/index.html'


class TreeView(DetailView):
    model = Collection
    template_name = 'viewer/collection-tree.html'
