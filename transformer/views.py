from django.urls import reverse
from rest_framework.decorators import detail_route
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response


from .models import Collection, Object, Agent, Term, TransformRun
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

    @detail_route()
    def identifiers(self, request, *args, **kwargs):
        collection = self.get_object()
        identifiers = Identifier.objects.filter(collection=collection)
        serializer = IdentifierSerializer(identifiers, context={'request': request}, many=True)
        return Response(serializer.data)

    @detail_route(url_path='identifiers/(?P<number>[0-9]+)')
    def identifiers_detail(self, request, number=None, *args, **kwargs):
        collection = self.get_object()
        if Identifier.objects.filter(id=number, collection=collection).exists():
            identifier = Identifier.objects.get(id=number, collection=collection)
            serializer = IdentifierSerializer(identifier, context={'request': request})
            return Response(serializer.data)
        return Response("Identifier not found", status=404)


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

    @detail_route()
    def identifiers(self, request, *args, **kwargs):
        object = self.get_object()
        identifiers = Identifier.objects.filter(object=object)
        serializer = IdentifierSerializer(identifiers, context={'request': request}, many=True)
        return Response(serializer.data)

    @detail_route(url_path='identifiers/(?P<number>[0-9]+)')
    def identifiers_detail(self, request, number=None, *args, **kwargs):
        object = self.get_object()
        if Identifier.objects.filter(id=number, object=object).exists():
            identifier = Identifier.objects.get(id=number, object=object)
            serializer = IdentifierSerializer(identifier, context={'request': request})
            return Response(serializer.data)
        return Response("Identifier not found", status=404)


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

    @detail_route()
    def identifiers(self, request, *args, **kwargs):
        agent = self.get_object()
        identifiers = Identifier.objects.filter(agent=agent)
        serializer = IdentifierSerializer(identifiers, context={'request': request}, many=True)
        return Response(serializer.data)

    @detail_route(url_path='identifiers/(?P<number>[0-9]+)')
    def identifiers_detail(self, request, number=None, *args, **kwargs):
        agent = self.get_object()
        if Identifier.objects.filter(id=number, agent=agent).exists():
            identifier = Identifier.objects.get(id=number, agent=agent)
            serializer = IdentifierSerializer(identifier, context={'request': request})
            return Response(serializer.data)
        return Response("Identifier not found", status=404)


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

    @detail_route()
    def identifiers(self, request, *args, **kwargs):
        term = self.get_object()
        identifiers = Identifier.objects.filter(term=term)
        serializer = IdentifierSerializer(identifiers, context={'request': request}, many=True)
        return Response(serializer.data)

    @detail_route(url_path='identifiers/(?P<number>[0-9]+)')
    def identifiers_detail(self, request, number=None, *args, **kwargs):
        agent = self.get_object()
        if Identifier.objects.filter(id=number, term=term).exists():
            identifier = Identifier.objects.get(id=number, term=term)
            serializer = IdentifierSerializer(identifier, context={'request': request})
            return Response(serializer.data)
        return Response("Identifier not found", status=404)


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


class TransformerRunView(APIView):
    """Runs transformation routines."""

    def post(self, request, format=None):
        source = request.GET.get('source')
        object_type = request.GET.get('object_type')
        try:
            if source:
                if source == 'archivesspace':
                    if object_type:
                        ArchivesSpaceDataTransformer(object_type).run()
                    else:
                        for object_type in ['agents', 'collections', 'objects', 'terms']:
                            ArchivesSpaceDataTransformer(object_type).run()
                elif source == 'cartographer':
                    CartographerDataTransformer().run()
                elif source == 'wikidata':
                    WikidataDataTransformer().run()
                elif source == 'wikipedia':
                    WikipediaDataTransformer().run()
                else:
                    return Response({"detail": "Unknown source {}.".format(source)}, status=400)
                message = ("Transformation routines complete for source {}.".format(source) if not object_type
                           else "Transformation routines complete for {} {}.".format(source, object_type))
                return Response({"detail": message}, status=200)
            else:
                for object_type in ['agents', 'collections', 'objects', 'terms']:
                    ArchivesSpaceDataTransformer(object_type).run()
                CartographerDataTransformer().run()
                WikidataDataTransformer().run()
                WikipediaDataTransformer().run()
                return Response({"detail": "Transformation routines complete for all sources and object types."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


class FindByIDView(APIView):
    """Gets objects by ID."""
    def get(self, request, format=None):
        source = request.GET.get('source')
        identifier = request.GET.get('identifier')
        if source and identifier:
            s = getattr(Identifier, source.upper())
            if Identifier.objects.filter(identifier=identifier, source=s).exists():
                identifier = Identifier.objects.get(identifier=identifier, source=s)
                results = []
                for relation in ['collection', 'object', 'agent', 'term']:
                    object = getattr(identifier, relation)
                    if object:
                        results.append({"ref": reverse("{}-detail".format(relation), kwargs={"pk": object.pk}), "type": relation})
                return Response(results, status=200)
            return Response({"detail": "Identifier {} from {} not found".format(identifier, source)}, status=404)
        return Response({"detail": "You must include both a source and an identifier as URL parameters"}, status=400)


class ImportRunView(APIView):
    """Runs import routine."""

    def post(self, request, format=None):
        try:
            import_fixture_data()
            return Response({"detail": "Import complete."}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
