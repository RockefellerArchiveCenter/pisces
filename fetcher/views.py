from asterism.views import prepare_response
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


class ArchivesSpaceFetchView(APIView):
    """Fetches list of objects to be updated or added."""

    def post(self, request, format=None):
        try:
            object_type = request.data.get('object_type')
            object_type_choices = [obj[0] for obj in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES]
            if object_type not in object_type_choices:
                return Response(
                    prepare_response(
                        "object_type must be one of {}, got {} instead".format(
                            object_type_choices,
                            object_type)
                        ), status=500
                    )
            resp = getattr(ArchivesSpaceDataFetcher(), "get_{}".format(self.action))(object_type=object_type)
            return Response(prepare_response(("{} {} data fetched".format(self.action, object_type), resp)), status=200)
        except Exception as e:
            return Response(prepare_response(str(e)), status=500)


class ArchivesSpaceUpdatesView(ArchivesSpaceFetchView):
    """Fetches list of objects to be updated or added."""
    action = "updated"


class ArchivesSpaceDeletesView(APIView):
    """Fetches list of objects to be deleted."""
    action = "deleted"
