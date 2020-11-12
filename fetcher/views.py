from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
        if self.action not in ["create", "retrieve", "update", "partial_update", "destroy"]:
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
    def subjects(self, request):
        return self.get_action_response(request, object_type="subject")

    @action(detail=False)
    def arrangement_map_components(self, request):
        return self.get_action_response(request, object_type="arrangement_map_component")
