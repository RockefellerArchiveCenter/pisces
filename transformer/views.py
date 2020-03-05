from asterism.views import BaseServiceView
from rest_framework.viewsets import ModelViewSet

from .models import DataObject
from .serializers import DataObjectListSerializer, DataObjectSerializer
from .transformers import Transformer


class TransformView(BaseServiceView):
    """Transforms source data."""

    def get_service_response(self, request):
        if not request.data:
            raise Exception("Missing request data")
        return Transformer().run(
            request.data.get("object_type"), request.data.get("object"))


class DataObjectViewSet(ModelViewSet):
    model = DataObject
    queryset = DataObject.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return DataObjectListSerializer
        return DataObjectSerializer
