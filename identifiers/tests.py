import random
import string
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from .models import Identifier, ExternalIdentifier
from .views import IdentifierViewSet


class IdentifiersTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.identifier_count = random.randint(1,10)

    def create_identifier(self):
        print('*** Creating identifiers ***')
        for i in range(self.identifier_count):
            request = self.factory.post(
                reverse('identifier-list'),
                {"source": random.choice(ExternalIdentifier.SOURCE_CHOICES),
                 "identifier": ''.join(random.choice(string.ascii_letters) for m in range(20))})
            response = IdentifierViewSet.as_view({'post': 'create'})(request)
            self.assertEqual(response.status_code, 200, "Wrong HTTP code")
        self.assertEqual(len(Identifier.objects.all()), self.identifier_count)

    def update_identifier(self):
        print('*** Updating identifiers ***')
        pk = random.choice(Identifier.objects.all()).pk
        request = self.factory.put(
            reverse('identifier-detail', kwargs={'pk': pk}),
            {"source": random.choice(ExternalIdentifier.SOURCE_CHOICES),
             "identifier": ''.join(random.choice(string.ascii_letters) for m in range(20))})
        response = IdentifierViewSet.as_view({'put': 'update'})(request, pk=pk)
        self.assertEqual(response.status_code, 200, "Wrong HTTP code")
        self.assertEqual(len(Identifier.objects.all()), self.identifier_count)

    def get_identifier(self):
        print('*** Getting identifiers ***')
        for identifier in Identifier.objects.all():
            pk = identifier.pk
            request = self.factory.get(reverse('identifier-detail', kwargs={'pk': pk}))
            response = IdentifierViewSet.as_view({'get': 'retrieve'})(request, pk=pk)
            self.assertEqual(response.status_code, 200, "Wrong HTTP code")

    def get_all_identifiers(self):
        print('*** Getting all identifiers ***')
        request = self.factory.get(reverse('identifier-list'))
        response = IdentifierViewSet.as_view({'get': 'list'})(request)
        self.assertEqual(response.status_code, 200, "Wrong HTTP code")
        self.assertEqual(len(response.data), self.identifier_count)

    def get_or_create_identifiers(self):
        print('*** Get or creating identifiers ***')
        request = self.factory.get(reverse('identifier-get-or-create'),
            {"source": random.choice(ExternalIdentifier.SOURCE_CHOICES),
             "identifier": ''.join(random.choice(string.ascii_letters) for m in range(20))})
        response = IdentifierViewSet.as_view({'get': 'list'})(request)
        self.assertEqual(response.status_code, 200, "Wrong HTTP code")

    def delete_identifier(self):
        print('*** Deleting identifiers ***')
        pk = random.choice(Identifier.objects.all()).pk
        request = self.factory.delete(
            reverse('identifier-detail', kwargs={'pk': pk}))
        response = IdentifierViewSet.as_view({'delete': 'destroy'})(request, pk=pk)
        self.assertEqual(response.status_code, 204, "Wrong HTTP code")

    def schema(self):
        print('*** Getting schema view ***')
        schema = self.client.get(reverse('schema-json', kwargs={"format": ".json"}))
        self.assertEqual(schema.status_code, 200, "Wrong HTTP code")

    def health_check(self):
        print('*** Getting status view ***')
        status = self.client.get(reverse('api_health_ping'))
        self.assertEqual(status.status_code, 200, "Wrong HTTP code")

    def test_identifiers(self):
        self.create_identifier()
        self.update_identifier()
        self.get_identifier()
        self.get_all_identifiers()
        self.get_or_create_identifiers()
        self.delete_identifier()
        self.schema()
        self.health_check()
