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


class ArchivesSpaceUpdatedView(APIView):
    """Fetches list of objects to be updated or added."""

    def post(self, request, format=None):
        try:
            object_type = request.data.get('object_type')
            if object_type not in ['resource', 'subject', 'archival_object', 'person', 'organization', 'family']:
                raise ArchivesSpaceDataFetcherError("Unknown object type {}".format(object_type))
            if not object_type:
                return Response({"detail": "Missing required field 'object_type' in request data"}, status=500)
            resp = ArchivesSpaceDataFetcher().get_updated(object_type=object_type)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
