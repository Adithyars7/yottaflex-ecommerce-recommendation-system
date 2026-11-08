import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from catalog.models import Category, Product
from tracking.models import Session, PageView
from orders.models import Cart, CartLine, Order, OrderLine
from recommendations.models import ProductRelation
from recommendations.services import save_recommendations


class Command(BaseCommand):
    help = "Generate synthetic e-commerce data for recommendation testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.random = random.Random(options["seed"])
        self.now = timezone.now()

        self.stdout.write("Starting synthetic data generation...")

        customers = self.create_customers()
        categories = self.create_categories()
        products = self.create_products(categories)

        sessions = self.create_sessions(customers, products)
        self.create_page_views(sessions, products)

        carts = self.create_carts(customers, sessions)
        self.create_cart_lines(carts, products)

        self.create_orders(customers, carts, products)
        self.create_product_relations(products)
        self.create_recommendations(customers, sessions)

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic data generation completed successfully!"
            )
        )

    def random_date(self, days=90):
        seconds = self.random.randint(0, days * 24 * 60 * 60)
        return self.now - timedelta(seconds=seconds)

    def create_customers(self):
        self.stdout.write("Creating customers...")

        customers = []

        first_names = [
            "Aarav", "Priya", "Rahul", "Ananya", "Rohan",
            "Neha", "Arjun", "Sneha", "Vikram", "Meera",
            "Kabir", "Isha", "Aditya", "Diya", "Karan",
        ]

        last_names = [
            "Sharma", "Patel", "Reddy", "Singh", "Kumar",
            "Mehta", "Rao", "Gupta", "Nair", "Das",
        ]

        for i in range(1, 101):
            email = f"synthetic{i:04d}@example.com"

            customer = Customer.objects.filter(email=email).first()

            if customer is None:
                customer = Customer.objects.create(
                    email=email,
                    first_name=self.random.choice(first_names),
                    last_name=self.random.choice(last_names),
                    is_active=True,
                )

            customers.append(customer)

        return customers

    def create_categories(self):
        self.stdout.write("Creating categories...")

        names = [
            "Electronics",
            "Fashion",
            "Home and Kitchen",
            "Books",
            "Sports",
            "Beauty",
            "Toys",
            "Grocery",
            "Footwear",
            "Accessories",
        ]

        categories = []

        for name in names:
            category = Category.objects.filter(name=name).first()

            if category is None:
                category = Category.objects.create(
                    name=name,
                    description=f"Synthetic category: {name}",
                )

            categories.append(category)

        return categories

    def create_products(self, categories):
        self.stdout.write("Creating products...")

        products = []

        for i in range(1, 51):
            name = f"Synthetic Product {i:03d}"

            product = Product.objects.filter(name=name).first()

            if product is None:
                category = self.random.choice(categories)

                product = Product.objects.create(
                    name=name,
                    description=f"Synthetic product number {i}",
                    category=category,
                    price=Decimal(
                        str(self.random.randint(199, 9999))
                    ),
                    is_available=(i % 10 != 0),
                    effective_from=self.now - timedelta(days=180),
                    effective_to=None,
                )

            products.append(product)

        return products

    def create_sessions(self, customers, products):
        self.stdout.write("Creating sessions...")

        sessions = []

        for i in range(500):
            customer = self.random.choice(customers)
            started_at = self.random_date()

            duration = timedelta(
                minutes=self.random.randint(5, 90)
            )

            ended_at = started_at + duration

            if ended_at > self.now:
                ended_at = self.now

            status = self.random.choice(
                ["COMPLETED", "COMPLETED", "EXPIRED", "ACTIVE"]
            )

            if status == "ACTIVE":
                ended_at = None

            session = Session.objects.create(
                customer=customer,
                started_at=started_at,
                ended_at=ended_at,
                status=status,
            )

            sessions.append(session)

        return sessions

    def create_page_views(self, sessions, products):
        self.stdout.write("Creating page views...")

        page_types = [
            "HOME",
            "PRODUCT",
            "CATEGORY",
            "CART",
            "CHECKOUT",
        ]

        for session in sessions:
            number_of_views = self.random.randint(2, 8)

            start = session.started_at

            if session.ended_at:
                end = session.ended_at
            else:
                end = self.now

            available_seconds = max(
                1,
                int((end - start).total_seconds()),
            )

            for _ in range(number_of_views):
                page_type = self.random.choice(page_types)

                event_at = start + timedelta(
                    seconds=self.random.randint(
                        0, available_seconds
                    )
                )

                product = None

                if page_type == "PRODUCT":
                    product = self.random.choice(products)

                PageView.objects.create(
                    session=session,
                    product=product,
                    page_type=page_type,
                    page_url=(
                        f"/products/{product.product_id}"
                        if product else "/"
                    ),
                    event_at=event_at,
                    recorded_at=event_at,
                )

    def create_carts(self, customers, sessions):
        self.stdout.write("Creating carts...")

        carts = []

        for _ in range(200):
            customer = self.random.choice(customers)

            customer_sessions = [
                session for session in sessions
                if session.customer_id == customer.pk
            ]

            session = (
                self.random.choice(customer_sessions)
                if customer_sessions else None
            )

            created_at = (
                session.started_at
                if session else self.random_date()
            )

            cart = Cart.objects.create(
                customer=customer,
                session=session,
                status=self.random.choice(
                    ["ACTIVE", "CONVERTED", "ABANDONED"]
                ),
                created_at=created_at,
                updated_at=created_at,
            )

            carts.append(cart)

        return carts

    def create_cart_lines(self, carts, products):
        self.stdout.write("Creating cart lines...")

        for cart in carts:
            selected_products = self.random