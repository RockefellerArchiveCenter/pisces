"""pisces URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from fetcher.views import (ArchivesSpaceDeletesView, ArchivesSpaceUpdatesView,
                           CartographerDeletesView, CartographerUpdatesView,
                           FetchRunViewSet)
from merger.views import MergeView
from rest_framework.schemas import get_schema_view
from transformer.views import DataObjectViewSet, TransformView

from .routers import PiscesRouter

router = PiscesRouter()
router.register(r'fetches', FetchRunViewSet, 'fetchrun')
router.register(r'objects', DataObjectViewSet, 'dataobject')

schema_view = get_schema_view(
    title="Pisces API",
    description="Endpoints for Pisces microservice application."
)


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^fetch/archivesspace/updates/$', ArchivesSpaceUpdatesView.as_view(), name='fetch-archivesspace-updates'),
    re_path(r'^fetch/archivesspace/deletes/$', ArchivesSpaceDeletesView.as_view(), name='fetch-archivesspace-deletes'),
    re_path(r'^fetch/cartographer/updates/$', CartographerUpdatesView.as_view(), name='fetch-cartographer-updates'),
    re_path(r'^fetch/cartographer/deletes/$', CartographerDeletesView.as_view(), name='fetch-cartographer-deletes'),
    re_path(r'^merge/$', MergeView.as_view(), name='merge'),
    re_path(r'^transform/$', TransformView.as_view(), name='transform'),
    re_path(r'^silk/', include('silk.urls', namespace='silk')),
    path('status/', include('health_check.api.urls')),
    path('schema/', schema_view, name='schema'),
    path('', include(router.urls)),
]
