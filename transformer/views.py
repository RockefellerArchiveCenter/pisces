from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .data_fetchers import ArchivesSpaceDataFetcher, WikidataDataFetcher, WikipediaDataFetcher
from .models import Collection, Object, Agent, Term, TransformRun, FetchRun
from .serializers import *
from .transformers import ArchivesSpaceDataTransformer, CartographerDataTransformer, WikidataDataTransformer, WikipediaDataTransformer
from .test_library import import_fixture_data


class CollectionViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a Collection, identified by a primary key.

    list:
    Return paginated data about all Collections.
    """
    model = Collection
    queryset = Collection.objects.all().order_by('-modified')

    def get_serializer_class(self):
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionSerializer


class ObjectViewSet(ModelViewSet):
    """
    retrieve:
    Return data about an Object, identified by a primary key.

    list:
    Return paginated data about all Objects.
    """
    model = Object
    queryset = Object.objects.all().order_by('-modified')

    def get_serializer_class(self):
        if self.action == 'list':
            return ObjectListSerializer
        return ObjectSerializer


class AgentViewSet(ModelViewSet):
    """
    retrieve:
    Return data about an Agent, identified by a primary key.

    list:
    Return paginated data about all Agents.
    """
    model = Agent
    queryset = Agent.objects.all().order_by('-modified')

    def get_serializer_class(self):
        if self.action == 'list':
            return AgentListSerializer
        return AgentSerializer


class TermViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a Term, identified by a primary key.

    list:
    Return paginated data about all Terms.
    """
    model = Term
    queryset = Term.objects.all().order_by('-modified')

    def get_serializer_class(self):
        if self.action == 'list':
            return TermListSerializer
        return TermSerializer


class TransformRunViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a TransformRun object, identified by a primary key.

    list:
    Return paginated data about all TranformRun objects.
    """
    model = TransformRun
    queryset = TransformRun.objects.all().order_by('-start_time')

    def get_serializer_class(self):
        if self.action == 'list':
            return TransformRunListSerializer
        return TransformRunSerializer


class FetchRunViewSet(ModelViewSet):
    """
    retrieve:
    Return data about a TransformRun object, identified by a primary key.

    list:
    Return paginated data about all TranformRun objects.
    """
    model = FetchRun
    queryset = FetchRun.objects.all().order_by('-start_time')

    def get_serializer_class(self):
        if self.action == 'list':
            return FetchRunListSerializer
        return FetchRunSerializer


class TransformerRunView(APIView):
    """Runs transformation routines."""

    def post(self, request, format=None):
        try:
            for object_type in ['agents', 'collections', 'objects', 'terms']:
                ArchivesSpaceDataTransformer(object_type).run()
            CartographerDataTransformer().run()
            WikidataDataTransformer().run()
            WikipediaDataTransformer().run()
            return Response({"detail": "Transformation routines complete."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class FetcherRunView(APIView):
    """Runs transformation routines."""

    def post(self, request, format=None):
        try:
            for object_type in ['agents', 'collections', 'objects', 'terms']:
                ArchivesSpaceDataFetcher(object_type).run()
            # WikidataDataTransformer().run()
            # WikipediaDataTransformer().run()
            return Response({"detail": "Fetcher routines complete."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class ImportRunView(APIView):
    """Runs import routine."""

    def post(self, request, format=None):
        try:
            import_fixture_data()
            return Response({"detail": "Import complete."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
