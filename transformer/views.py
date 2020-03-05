from asterism.views import BaseServiceView

from .transformers import Transformer


class TransformView(BaseServiceView):
    """Transforms source data."""

    def get_service_response(self, request):
        if not request.data:
            raise Exception("Missing request data")
        return Transformer().run(
            request.data.get("object_type"), request.data.get("object"))
