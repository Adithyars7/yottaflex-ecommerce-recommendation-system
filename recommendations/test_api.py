from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from customers.models import Customer
from catalog.models import Category, Product
from tracking.models import Session, PageView


class RecommendationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.now = timezone.now()

        self.customer = Customer.objects.create(
            email="api.test@example.com",
            first_name="API",
            last_name="Tester",
            is_active=True,
        )

        self.other_customer = Customer.objects.create(
            email="other.api.test@example.com",
            first_name="Other",
            last_name="Customer",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="API Test Electronics",
            description="Category for API testing",
        )

        self.product = Product.objects.create(
            name="API Test Headphones",
            description="Product for API testing",
            category=self.category,
            price=Decimal("1999.00"),
            is_available=True,
            effective_from=self.now - timedelta(days=10),
            effective_to=None,
        )

        self.session = Session.objects.create(
            customer=self.customer,
            started_at=self.now - timedelta(hours=1),
            status="ACTIVE",
        )

        PageView.objects.create(
            session=self.session,
            product=self.product,
            page_type="PRODUCT",
            page_url="/products/api-test-headphones",
            event_at=self.now - timedelta(minutes=30),
        )

        self.url = reverse(
            "customer-recommendations",
            kwargs={
                "customer_id": self.customer.customer_id,
            },
        )

    def test_valid_customer_receives_recommendations(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["customer_id"],
            self.customer.customer_id,
        )

        self.assertEqual(
            response.data["total_recommendations"],
            1,
        )

        self.assertEqual(
            response.data["recommendations"][0]["product"]["name"],
            "API Test Headphones",
        )

    def test_nonexistent_customer_returns_404(self):
        url = reverse(
            "customer-recommendations",
            kwargs={
                "customer_id": "CUS-999999",
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_limit_returns_400(self):
        response = self.client.get(
            self.url,
            {"limit": "invalid"},
        )

        self.assertEqual(response.status_code, 400)

    def test_limit_outside_allowed_range_returns_400(self):
        response = self.client.get(
            self.url,
            {"limit": "100"},
        )

        self.assertEqual(response.status_code, 400)

    def test_session_belonging_to_another_customer_returns_404(self):
        other_session = Session.objects.create(
            customer=self.other_customer,
            started_at=self.now - timedelta(hours=1),
            status="ACTIVE",
        )

        response = self.client.get(
            self.url,
            {"session_id": other_session.session_id},
        )

        self.assertEqual(response.status_code, 404)