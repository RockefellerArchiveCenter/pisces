import urllib

from asterism.views import prepare_response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .fetchers import ArchivesSpaceDataFetcher, CartographerDataFetcher
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


class BaseFetchView(APIView):
    def post(self, request, format=None):
        try:
            object_type = request.GET.get('object_type')
            post_service_url = self.get_post_service_url(request)
            if object_type not in self.object_type_choices:
                return Response(
                    prepare_response(
                        "object_type must be one of {}, got {} instead".format(
                            self.object_type_choices,
                            object_type)
                    ), status=500
                )
            resp = self.fetcher_class().fetch(self.status, object_type, post_service_url)
            return Response(
                prepare_response(
                    ("{} {} data fetched".format(self.status, object_type), resp)
                ), status=200)
        except Exception as e:
            return Response(prepare_response(str(e)), status=500)

    def get_post_service_url(self, request):
        url = request.GET.get('post_service_url')
        return urllib.parse.unquote(url) if url else ''


class ArchivesSpaceFetchView(BaseFetchView):
    """
    Base ArchivesSpace fetcher view which provides a fetcher class and
    object type choices.
    """
    fetcher_class = ArchivesSpaceDataFetcher
    object_type_choices = [obj[0] for obj in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES]


class ArchivesSpaceUpdatesView(ArchivesSpaceFetchView):
    """Fetches list of objects to be updated or added."""
    status = "updated"


class ArchivesSpaceDeletesView(ArchivesSpaceFetchView):
    """Fetches list of objects to be deleted."""
    status = "deleted"


class CartographerFetchView(BaseFetchView):
    """
    Base Cartographer fetcher view which provides a fetcher class and
    object type choices.
    """
    fetcher_class = CartographerDataFetcher
    object_type_choices = [obj[0] for obj in FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES]


class CartographerUpdatesView(CartographerFetchView):
    """Fetches list of objects to be updated or added."""
    status = "updated"


class CartographerDeletesView(CartographerFetchView):
    """Fetches list of objects to be deleted."""
    status = "deleted"
