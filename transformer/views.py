from asterism.views import BaseServiceView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import DataObject
from .serializers import DataObjectListSerializer, DataObjectSerializer


class DataObjectViewSet(ModelViewSet):
    model = DataObject

    def get_queryset(self, request):
        queryset = DataObject.objects.all().order_by("last_modified")
        if request.GET.get("clean", "").lower() != "true":
            queryset = queryset.exclude(indexed=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return DataObjectListSerializer
        return DataObjectSerializer

    def get_action_response(self, request, object_type):
        queryset = self.get_action_queryset(request, object_type)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_action_queryset(self, request, object_type):
        queryset = DataObject.objects.filter(object_type=object_type).order_by("last_modified")
        if request.GET.get("clean", "").lower() != "true":
            queryset = queryset.exclude(indexed=True)
        return queryset

    @action(detail=False)
    def agents(self, request):
        return self.get_action_response(request, "agent")

    @action(detail=False)
    def collections(self, request):
        return self.get_action_response(request, "collection")

    @action(detail=False)
    def objects(self, request):
        return self.get_action_response(request, "object")

    @action(detail=False)
    def terms(self, request):
        return self.get_action_response(request, "term")


class DataObjectUpdateByIdView(BaseServiceView):
    """Updates DataObjects after they have been indexed.

    Finds a DataObject by its es_id field and sets indexed to True.
    """

    def get_service_response(self, request):
        es_id = request.data.get("identifier")
        action = request.data.get("action")
        if action not in ["deleted", "indexed"]:
            raise Exception("Unrecognized action {}, expecting either `deleted` or `indexed`")
        try:
            obj = DataObject.objects.get(es_id=es_id)
            if action == "indexed":
                obj.indexed = True
                obj.save()
                msg = "{} {} marked as indexed.".format(obj.object_type, obj.pk)
            else:
                obj.delete()
                msg = "{} {} deleted.".format(obj.object_type, obj.pk)
        except DataObject.DoesNotExist:
            raise Exception("Could not find DataObject with identifier {}".format(es_id))
        return msg
