from asterism.views import BaseServiceView
from rest_framework.decorators import action
from rest_framework.response import Response
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
    queryset = FetchRun.objects.all().order_by("-start_time")

    def get_serializer_class(self):
        if self.action == "list":
            return FetchRunListSerializer
        return FetchRunSerializer

    def get_action_response(self, request, object_type=None, source=None):
        queryset = self.get_action_queryset(request, object_type, source)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_action_queryset(self, request, object_type, source):
        if object_type:
            queryset = FetchRun.objects.filter(object_type=object_type)
        if source is not None:
            queryset = FetchRun.objects.filter(source=source)
        return queryset.order_by("-start_time")

    @action(detail=False)
    def archivesspace(self, request):
        return self.get_action_response(request, source=FetchRun.ARCHIVESSPACE)

    @action(detail=False)
    def cartographer(self, request):
        return self.get_action_response(request, source=FetchRun.CARTOGRAPHER)

    @action(detail=False)
    def archival_objects(self, request):
        return self.get_action_response(request, object_type="archival_object")

    @action(detail=False)
    def people(self, request):
        return self.get_action_response(request, object_type="agent_person")

    @action(detail=False)
    def organizations(self, request):
        return self.get_action_response(request, object_type="agent_corporate_entity")

    @action(detail=False)
    def families(self, request):
        return self.get_action_response(request, object_type="agent_family")

    @action(detail=False)
    def resources(self, request):
        return self.get_action_response(request, object_type="resource")

    @action(detail=False)
    def arrangement_map_components(self, request):
        return self.get_action_response(request, object_type="arrangement_map_component")


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
