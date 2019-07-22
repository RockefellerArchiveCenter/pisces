from django.urls import path, re_path
from .views import *

app_name = 'api'
urlpatterns = [
    re_path('collections/$', CollectionListView.as_view(), name='collection-list'),
    re_path('collections/(?P<id>[-\w]+)', CollectionDetailView.as_view(), name='collection-detail'),
    re_path('objects/$', ObjectListView.as_view(), name='object-list'),
    re_path('objects/(?P<id>[-\w]+)', ObjectDetailView.as_view(), name='object-detail'),
    re_path('agents/$', AgentListView.as_view(), name='agent-list'),
    re_path('agents/(?P<id>[-\w]+)', AgentDetailView.as_view(), name='agent-detail'),
    re_path('terms/$', TermListView.as_view(), name='term-list'),
    re_path('terms/(?P<id>[-\w]+)', TermDetailView.as_view(), name='term-detail'),
    re_path('$', IndexView.as_view(), name='index')
]
