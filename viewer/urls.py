from django.urls import path, re_path
from .views import *

app_name = 'app'
urlpatterns = [
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    re_path('collections/(?P<pk>\d+)/tree', TreeView.as_view(), name='collection-tree'),
    re_path('collections/(?P<pk>\d+)', CollectionDetailView.as_view(), name='collection-detail'),
    re_path('objects/(?P<pk>\d+)', ObjectDetailView.as_view(), name='object-detail'),
    path('agents/', AgentListView.as_view(), name='agent-list'),
    re_path('agents/(?P<pk>\d+)', AgentDetailView.as_view(), name='agent-detail'),
    path('terms/', TermListView.as_view(), name='term-list'),
    re_path('terms/(?P<pk>\d+)', TermDetailView.as_view(), name='term-detail'),
    re_path('$', IndexView.as_view(), name='index')
]
