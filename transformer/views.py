from rest_framework.views import APIView
from rest_framework.response import Response

from .transformers import ArchivesSpaceDataTransformer


class ArchivesSpaceTransformView(APIView):
    """Transforms ArchivesSpace data."""

    def post(self, request, format=None):
        try:
            if not request.data:
                print("no data")
                return Response({"detail": "Missing request data"}, status=500)
            resp = ArchivesSpaceDataTransformer().run(request.data)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
