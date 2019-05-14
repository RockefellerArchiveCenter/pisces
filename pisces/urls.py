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
from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from transformer.views import *

router = routers.DefaultRouter()
router.register(r'agents', AgentViewSet, 'agent')
router.register(r'collections', CollectionViewSet, 'collection')
router.register(r'objects', ObjectViewSet, 'object')
router.register(r'terms', TermViewSet, 'term')
router.register(r'transforms', TransformRunViewSet, 'transformrun')
schema_view = get_schema_view(
   openapi.Info(
      title="Pisces API",
      default_version='v1',
      description="API for Pisces",
      contact=openapi.Contact(email="archive@rockarch.org"),
      license=openapi.License(name="MIT License"),
   ),
   validators=['flex', 'ssv'],
   public=False,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('find-by-id/', FindByIDView.as_view(), name='find-by-id'),
    path('transform/', TransformerRunView.as_view(), name='transform-data'),
    path('import/', ImportRunView.as_view(), name='import-data'),
    path('status/', include('health_check.api.urls')),
    re_path(r'^schema(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None), name='schema-json'),
    path('api/', include(router.urls)),
    path('', include('viewer.urls')),
]
