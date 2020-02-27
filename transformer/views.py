from asterism.views import BaseServiceView

from .transformers import ArchivesSpaceDataTransformer


class ArchivesSpaceTransformView(BaseServiceView):
    """Takes the get request for AS data and returns a web response based on the transformation of that data."""

    def get_service_response(self, request):
        if not request.data:
            raise Exception("Missing request data")
        return ArchivesSpaceDataTransformer().run(request.data)


class CartographerTransformView(BaseServiceView):
    """Takes the get request for AS data and returns a web response based on the transformation of that data."""

    def get_service_response(self, request):
        if not request.data:
            raise Exception("Missing request data")
        return "success"
