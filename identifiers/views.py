from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Identifier, ExternalIdentifier
from .serializers import IdentifierSerializer, IdentifierListSerializer
from pisces import settings


class IdentifierValidationError(Exception): pass


class IdentifierViewSet(ModelViewSet):
    """
    retrieve:
    Return data about an identifier, identified by a primary key.

    list:
    Return paginated data about all identifiers.

    create:
    Create a new identifier.
    Requires a payload which specifies an external identifier.

    update:
    Update an existing identifier, identified by a primary key.
    """
    model = Identifier
    queryset = Identifier.objects.all().order_by('-created')

    def get_serializer_class(self):
        if self.action == 'list':
            return IdentifierListSerializer
        return IdentifierSerializer

    def _validate_data(self, data):
        if not all(k in data for k in ['source', 'identifier']):
            raise IdentifierValidationError("missing key: {}".format(k))
        if not any(data.get('source') == s[1] for s in ExternalIdentifier.SOURCE_CHOICES):
            raise IdentifierValidationError("invalid source: {}".format(data.get('source')))
        if ExternalIdentifier.objects.filter(
                source=data.get('source'), source_identifier=data.get('identifier')).exists():
            raise IdentifierValidationError("identifier already exists")

    def create(self, request):
        try:
            self._validate_data(request.data)
            identifier = Identifier.objects.create()
            ExternalIdentifier.objects.create(
                identifier=identifier,
                source=request.data.get('source'),
                source_identifier=request.data.get('identifier')
            )
            serialized = IdentifierSerializer(identifier, context={'request': request})
            return Response(serialized.data)
        except IdentifierValidationError as e:
            return Response({"detail": "Invalid data: {}".format(e)}, status=400)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=500)

    def update(self, request, pk):
        try:
            self._validate_data(request.data)
            identifier = Identifier.objects.get(pk=pk)
            ExternalIdentifier.objects.create(
                identifier=identifier,
                source=request.data.get('source'),
                source_identifier=request.data.get('identifier')
            )
            serialized = IdentifierSerializer(identifier, context={'request': request})
            return Response(serialized.data)
        except IdentifierValidationError as e:
            return Response({"detail": "Invalid data: {}".format(e)}, status=400)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def get_or_create(self, request):
        for k in ['source', 'identifier']:
            if k not in request.GET:
                return Response({'detail': 'Missing URL parameter: {}'.format(k)})
        if ExternalIdentifier.objects.filter(source=request.GET.get('source'), source_identifier=request.GET.get('identifier')).exists():
            external_identifier = ExternalIdentifier.objects.get(source=request.GET.get('source'), source_identifier=request.GET.get('identifier'))
            identifier = external_identifier.identifier
            serialized = IdentifierSerializer(identifier, context={'request': request})
            return Response(serialized.data)
        try:
            self._validate_data(request.GET)
            identifier = Identifier.objects.create()
            ExternalIdentifier.objects.create(
                identifier=identifier,
                source=request.GET.get('source'),
                source_identifier=request.GET.get('identifier')
            )
            serialized = IdentifierSerializer(identifier, context={'request': request})
            return Response(serialized.data)
        except IdentifierValidationError as e:
            return Response({"detail": "Invalid data: {}".format(e)}, status=400)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=500)
