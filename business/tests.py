from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from business.models import BusinessType, Business
from staff.models import Staff


class BusinessRegisterAPITests(APITestCase):
    def setUp(self):
        self.business_type = BusinessType.objects.create(name="Nail Salon")
        self.url = "/api/business/auth/register/"

    def test_register_business_success(self):
        payload = {
            "business": {
                "name": "Test Salon",
                "business_type": str(self.business_type.id),
                "phone": "15550001",
                "email": "info1@luxenails.com",
                "city": "Toronto",
                "country": "Canada",
            },
            "owner": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "info1@luxenails.com",
                "phone": "15550001",
            },
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get("success"))
        results = response.data.get("results") or {}


        self.assertIsNotNone(results)

        user_data = results.get("user")
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["first_name"], "John")
        self.assertEqual(user_data["last_name"], "Doe")
        self.assertEqual(user_data["email"], "info1@luxenails.com")
        self.assertEqual(user_data["phone"], "15550001")

        tokens = results.get("tokens")
        self.assertIsNotNone(tokens)
        self.assertIsNotNone(tokens.get("refresh"))
        self.assertIsNotNone(tokens.get("access"))