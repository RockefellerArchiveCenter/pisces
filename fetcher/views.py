from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .fetchers import ArchivesSpaceDataFetcher
from .models import FetchRun
from .serializers import FetchRunSerializer, FetchRunListSerializer


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
