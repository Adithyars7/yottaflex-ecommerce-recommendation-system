from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from customers.models import Customer
from catalog.models import Category, Product
from tracking.models import Session, PageView
from orders.models import Cart, CartLine, Order, OrderLine

from recommendations.services import (
    get_available_products,
    get_customer_activity,
)


class RecommendationEngineTests(TestCase):

    def setUp(self):
        self.now = timezone.now()

        self.customer = Customer.objects.create(
            email="recommendation.test@example.com",
            first_name="Test",
            last_name="Customer",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Test Electronics",
            description="Category for recommendation tests",
        )

        self.available_product = Product.objects.create(
            name="Available Test Product",
            description="An available product",
            category=self.category,
            price=Decimal("1000.00"),
            is_available=True,
            effective_from=self.now - timedelta(days=10),
            effective_to=None,
        )

        self.unavailable_product = Product.objects.create(
            name="Unavailable Test Product",
            description="An unavailable product",
            category=self.category,
            price=Decimal("1500.00"),
            is_available=False,
            effective_from=self.now - timedelta(days=10),
            effective_to=None,
        )

        self.future_product = Product.objects.create(
            name="Future Test Product",
            description="A product not yet active",
            category=self.category,
            price=Decimal("2000.00"),
            is_available=True,
            effective_from=self.now + timedelta(days=5),
            effective_to=None,
        )

        self.expired_product = Product.objects.create(
            name="Expired Test Product",
            description="An expired product",
            category=self.category,
            price=Decimal("500.00"),
            is_available=True,
            effective_from=self.now - timedelta(days=20),
            effective_to=self.now - timedelta(days=1),
        )

    def test_unavailable_products_are_excluded(self):
        """
        Unavailable, expired and future products
        must not appear in eligible products.
        """

        products = get_available_products(self.now)

        product_ids = set(
            products.values_list("pk", flat=True)
        )

        self.assertIn(
            self.available_product.pk,
            product_ids,
        )

        self.assertNotIn(
            self.unavailable_product.pk,
            product_ids,
        )

        self.assertNotIn(
            self.future_product.pk,
            product_ids,
        )

        self.assertNotIn(
            self.expired_product.pk,
            product_ids,
        )

    def test_future_page_views_are_excluded(self):
        """
        Page views after the recommendation timestamp
        must not be included in customer activity.
        """

        session = Session.objects.create(
            customer=self.customer,
            started_at=self.now - timedelta(days=1),
            ended_at=None,
            status="ACTIVE",
        )

        PageView.objects.create(
            session=session,
            product=self.available_product,
            page_type="PRODUCT",
            page_url="/products/available",
            event_at=self.now - timedelta(hours=1),
        )

        PageView.objects.create(
            session=session,
            product=self.unavailable_product,
            page_type="PRODUCT",
            page_url="/products/future-event",
            event_at=self.now + timedelta(hours=1),
        )

        activity = get_customer_activity(
            self.customer,
            self.now,
        )

        viewed_product_ids = set(
            activity["page_views"].values_list(
                "product_id",
                flat=True,
            )
        )

        self.assertIn(
            self.available_product.pk,
            viewed_product_ids,
        )

        self.assertNotIn(
            self.unavailable_product.pk,
            viewed_product_ids,
        )

    def test_future_cart_and_order_activity_are_excluded(self):
        """
        Cart lines and orders created after the recommendation
        timestamp must not influence customer activity.
        """

        # Create a cart.
        cart = Cart.objects.create(
            customer=self.customer,
            status="ACTIVE",
        )

        # Set its creation time to before recommendation time.
        Cart.objects.filter(pk=cart.pk).update(
            created_at=self.now - timedelta(hours=2)
        )

        # Create a cart line.
        cart_line = CartLine.objects.create(
            cart=cart,
            product=self.available_product,
            quantity=2,
        )

        # Set the cart line addition time to the future.
        CartLine.objects.filter(pk=cart_line.pk).update(
            added_at=self.now + timedelta(hours=1)
        )

        # Create an order placed in the future.
        order = Order.objects.create(
            customer=self.customer,
            status="CONFIRMED",
            placed_at=self.now + timedelta(hours=1),
        )

        # Create an order line.
        order_line = OrderLine.objects.create(
            order=order,
            product=self.available_product,
            quantity=1,
            unit_price=self.available_product.price,
            product_name_snapshot=self.available_product.name,
        )

        activity = get_customer_activity(
            self.customer,
            self.now,
        )

        # The cart existed before recommendation time.
        self.assertIn(
            cart.pk,
            activity["carts"].values_list("pk", flat=True),
        )

        # The future cart line must be excluded.
        self.assertFalse(
            activity["cart_lines"].filter(
                pk=cart_line.pk
            ).exists()
        )

        # The future order must be excluded.
        self.assertFalse(
            activity["orders"].filter(
                pk=order.pk
            ).exists()
        )

        # Its order line must also be excluded.
        self.assertFalse(
            activity["order_lines"].filter(
                pk=order_line.pk
            ).exists()
        )