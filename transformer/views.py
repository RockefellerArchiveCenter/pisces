from asterism.views import BaseServiceView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import DataObject
from .serializers import DataObjectListSerializer, DataObjectSerializer


class DataObjectViewSet(ModelViewSet):
    model = DataObject

    def get_queryset(self):
        queryset = DataObject.objects.all().order_by("last_modified")
        if self.request.GET.get("clean", "").lower() != "true":
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
        identifiers = request.data.get("identifiers")
        action = request.data.get("action")
        msg = "No object identifiers were found."
        if action not in ["deleted", "indexed"]:
            raise Exception("Unrecognized action {}, expecting either `deleted` or `indexed`")
        obj_list = DataObject.objects.filter(es_id__in=identifiers)
        if action == "indexed":
            for obj in obj_list:
                obj.indexed = True
            DataObject.objects.bulk_update(obj_list, ["indexed"])
        else:
            for obj in obj_list:
                try:
                    obj.delete()
                except DataObject.DoesNotExist:
                    pass
        msg = "{} {} {}.".format(
            len(obj_list), obj.object_type,
            "marked as indexed." if action == "indexed" else "deleted")
        return msg
