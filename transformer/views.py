from django.urls import reverse
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .fetchers import *
from .models import FetchRun
from .serializers import *
from .transformers import *
from .test_library import import_fixture_data


class FetchRunViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a FetchRun object, identified by a primary key.

    list:
    Return paginated data about all FetchRun objects.
    """
    model = FetchRun
    queryset = FetchRun.objects.all().order_by('-start_time')

    def get_serializer_class(self):
        if self.action == 'list':
            return FetchRunListSerializer
        return FetchRunSerializer


class ArchivesSpaceFetchChangesView(APIView):
    """Fetches list of objects to be updated or deleted."""

    def post(self, request, format=None):
        try:
            object_type = request.data.get('object_type')
            if not object_type:
                return Response({"detail": "Missing required field 'object_type' in request data"}, status=500)
            resp = ArchivesSpaceDataFetcher().changes(object_type=object_type)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class ArchivesSpaceFetchURIView(APIView):
    """Fetches a data object by URI."""

    def post(self, request, format=None):
        try:
            data = request.data.get('data')
            if not data:
                return Response({"detail": "Missing required field 'data' in request data"}, status=500)
            resp = ArchivesSpaceDataFetcher().from_uri(data)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class ArchivesSpaceTransformView(APIView):
    """Transforms ArchivesSpace data."""

    def post(self, request, format=None):
        try:
            data = request.data.get('data')
            if not data:
                return Response({"detail": "Missing required field 'data' in request data"}, status=500)
            resp = ArchivesSpaceDataTransformer().run(data)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class FindByIDView(APIView):
    """Gets objects by ID."""
    def get(self, request, format=None):
        source = getattr(Identifier, request.GET.get('source').upper()) if request.GET.get('source') else None
        identifier = request.GET.get('identifier')
        if source and identifier:
            if Identifier.objects.filter(identifier=identifier, source=source).exists():
                identifier = Identifier.objects.get(identifier=identifier, source=source)
                data = {"count": 0, "results": []}
                for relation in ['collection', 'object', 'agent', 'term']:
                    object = getattr(identifier, relation)
                    if object:
                        data['results'].append({"ref": reverse("{}-detail".format(relation), kwargs={"pk": object.pk}), "type": relation})
                        data['count'] += 1
                return Response(data, status=200)
            return Response({"detail": "Identifier {} from {} not found".format(identifier, source)}, status=404)
        return Response({"detail": "You must include both a source and an identifier as URL parameters"}, status=400)


class ImportRunView(APIView):
    """Runs import routine."""

    def post(self, request, format=None):
        try:
            import_fixture_data()
            return Response({"detail": "Import complete."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
