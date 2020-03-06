from asterism.views import BaseServiceView
from rest_framework.viewsets import ModelViewSet

from .fetchers import ArchivesSpaceDataFetcher, CartographerDataFetcher
from .models import FetchRun
from .serializers import FetchRunListSerializer, FetchRunSerializer


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


class BaseFetchView(BaseServiceView):
    """Base view for data fetchers.

    Accepts only POST requests. Delegates to a data fetcher which targets a
    specific data source and object type. Object type are parsed from request
    parameters, such as `?object_type=resource`.
    """

    def get_service_response(self, request):
        object_type = request.GET.get('object_type')
        if object_type not in self.object_type_choices:
            raise Exception(
                "object_type must be one of {}, got {} instead".format(
                    self.object_type_choices, object_type))
        resp = self.fetcher_class().fetch(self.status, object_type)
        return "{} {} data fetched".format(self.status, object_type), resp


class ArchivesSpaceFetchView(BaseFetchView):
    """Base ArchivesSpace fetcher view.

    Provides a fetcher class and object type choices which are inherited by all
    ArchivesSpace fetchers.
    """
    fetcher_class = ArchivesSpaceDataFetcher
    object_type_choices = [obj[0] for obj in FetchRun.ARCHIVESSPACE_OBJECT_TYPE_CHOICES]


class ArchivesSpaceUpdatesView(ArchivesSpaceFetchView):
    """Fetches list of new or updated ArchivesSpace objects."""
    status = "updated"


class ArchivesSpaceDeletesView(ArchivesSpaceFetchView):
    """Fetches list of deleted ArchivesSpace objects."""
    status = "deleted"


class CartographerFetchView(BaseFetchView):
    """Base Cartographer fetcher view.

    Provides a fetcher class and object type choices which are inherited by all
    Cartographer fetchers.
    """
    fetcher_class = CartographerDataFetcher
    object_type_choices = [obj[0] for obj in FetchRun.CARTOGRAPHER_OBJECT_TYPE_CHOICES]


class CartographerUpdatesView(CartographerFetchView):
    """Fetches list of new or updated Cartographer objects."""
    status = "updated"


class CartographerDeletesView(CartographerFetchView):
    """Fetches list of deleted Cartographer objects."""
    status = "deleted"
