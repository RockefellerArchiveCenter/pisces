from rest_framework.views import APIView
from rest_framework.response import Response

from .transformers import ArchivesSpaceDataTransformer


class ArchivesSpaceTransformView(APIView):
    """Takes the get request for AS data and returns a web response based on the transformation of that data."""

    def post(self, request, format=None):
        try:
            data = request.data.get('data')
            if not data:
                return Response({"detail": "Missing required field 'data' in request data"}, status=500)
            resp = ArchivesSpaceDataTransformer().run(data)
            return Response(resp, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
