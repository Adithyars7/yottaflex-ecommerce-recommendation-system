from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q

from customers.models import Customer
from catalog.models import Category, Product
from tracking.models import Session, PageView
from orders.models import Cart, CartLine, Order, OrderLine
from recommendations.models import ProductRelation, Recommendation


class Command(BaseCommand):
    help = "Validate synthetic e-commerce data integrity."

    def handle(self, *args, **options):
        self.errors = []
        self.warnings = []

        self.stdout.write("Starting data validation...\n")

        self.check_id_formats()
        self.check_duplicates()
        self.check_relationships()
        self.check_timestamps()
        self.check_recommendations()

        self.stdout.write("\n========== VALIDATION SUMMARY ==========")

        if self.errors:
            self.stdout.write(
                self.style.ERROR(f"Errors found: {len(self.errors)}")
            )

            for error in self.errors:
                self.stdout.write(self.style.ERROR(f"- {error}"))
        else:
            self.stdout.write(
                self.style.SUCCESS("No validation errors found.")
            )

        if self.warnings:
            self.stdout.write(
                self.style.WARNING(f"Warnings: {len(self.warnings)}")
            )

            for warning in self.warnings:
                self.stdout.write(
                    self.style.WARNING(f"- {warning}")
                )

        self.stdout.write("\n========== TABLE COUNTS ==========")

        models_to_check = [
            ("Customers", Customer),
            ("Categories", Category),
            ("Products", Product),
            ("Sessions", Session),
            ("PageViews", PageView),
            ("Carts", Cart),
            ("CartLines", CartLine),
            ("Orders", Order),
            ("OrderLines", OrderLine),
            ("ProductRelations", ProductRelation),
            ("Recommendations", Recommendation),
        ]

        for name, model in models_to_check:
            self.stdout.write(f"{name}: {model.objects.count()}")

        if self.errors:
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS("\nData validation completed.")
        )

    def check_id_formats(self):
        self.stdout.write("Checking ID formats...")

        checks = [
            (Customer, "customer_id", "CUS-"),
            (Category, "category_id", "CAT-"),
            (Product, "product_id", "SKU-"),
            (CartLine, "cart_line_id", "CL-"),
            (OrderLine, "order_line_id", "OL-"),
            (ProductRelation, "relation_id", "REL-"),
            (Recommendation, "recommendation_id", "REC-"),
        ]

        for model, field, prefix in checks:
            invalid = model.objects.exclude(
                **{f"{field}__startswith": prefix}
            ).count()

            if invalid:
                self.add_error(
                    f"{model.__name__}: {invalid} invalid IDs."
                )

        for session in Session.objects.all().only(
            "session_id", "started_at"
        ):
            expected = (
                f"SES-{session.started_at.year}-{session.pk:06d}"
            )

            if session.session_id != expected:
                self.add_error(
                    f"Session {session.pk} has an invalid ID."
                )

        for cart in Cart.objects.all().only(
            "cart_id", "created_at"
        ):
            expected = (
                f"CART-{cart.created_at.year}-{cart.pk:06d}"
            )

            if cart.cart_id != expected:
                self.add_error(
                    f"Cart {cart.pk} has an invalid ID."
                )

        for order in Order.objects.all().only(
            "order_id", "placed_at"
        ):
            expected = (
                f"ORD-{order.placed_at.year}-{order.pk:06d}"
            )

            if order.order_id != expected:
                self.add_error(
                    f"Order {order.pk} has an invalid ID."
                )

        for event in PageView.objects.select_related(
            "session"
        ).only("event_id", "session__session_id"):
            expected_prefix = f"EVT-{event.session.session_id}-"

            if not event.event_id.startswith(expected_prefix):
                self.add_error(
                    f"PageView {event.pk} has an invalid event ID."
                )

    def check_duplicates(self):
        self.stdout.write("Checking duplicate IDs...")

        checks = [
            (Customer, "customer_id"),
            (Category, "category_id"),
            (Product, "product_id"),
            (Session, "session_id"),
            (PageView, "event_id"),
            (Cart, "cart_id"),
            (CartLine, "cart_line_id"),
            (Order, "order_id"),
            (OrderLine, "order_line_id"),
            (ProductRelation, "relation_id"),
            (Recommendation, "recommendation_id"),
        ]

        for model, field in checks:
            duplicates = (
                model.objects.values(field)
                .annotate(total=Count("pk"))
                .filter(total__gt=1)
                .count()
            )

            if duplicates:
                self.add_error(
                    f"{model.__name__}: {duplicates} duplicate IDs."
                )

    def check_relationships(self):
        self.stdout.write("Checking relationships...")

        mismatched_carts = Cart.objects.filter(
            session__isnull=False,
            session__customer__isnull=False,
        ).exclude(
            customer_id=F("session__customer_id")
        ).count()

        if mismatched_carts:
            self.add_error(
                f"{mismatched_carts} carts have mismatched session customers."
            )

        mismatched_orders = Order.objects.filter(
            cart__isnull=False
        ).exclude(
            customer_id=F("cart__customer_id")
        ).count()

        if mismatched_orders:
            self.add_error(
                f"{mismatched_orders} orders have mismatched cart customers."
            )

    def check_timestamps(self):
        self.stdout.write("Checking timestamps...")

        invalid_sessions = Session.objects.filter(
            ended_at__lt=F("started_at")
        ).count()

        if invalid_sessions:
            self.add_error(
                f"{invalid_sessions} sessions end before they start."
            )

        invalid_page_views = PageView.objects.filter(
            event_at__lt=F("session__started_at")
        ).count()

        if invalid_page_views:
            self.add_error(
                f"{invalid_page_views} page views occur before their sessions."
            )

        invalid_cart_lines = CartLine.objects.filter(
            added_at__lt=F("cart__created_at")
        ).count()

        if invalid_cart_lines:
            self.add_error(
                f"{invalid_cart_lines} cart lines precede their carts."
            )

        invalid_orders = Order.objects.filter(
            cart__isnull=False,
            placed_at__lt=F("cart__created_at"),
        ).count()

        if invalid_orders:
            self.add_error(
                f"{invalid_orders} orders precede their carts."
            )

        invalid_recommendations = Recommendation.objects.filter(
            expires_at__isnull=False,
            expires_at__lte=F("generated_at"),
        ).count()

        if invalid_recommendations:
            self.add_error(
                f"{invalid_recommendations} recommendations have invalid expiry dates."
            )

    def check_recommendations(self):
        self.stdout.write("Checking recommendation eligibility...")

        invalid = Recommendation.objects.filter(
            Q(product__is_available=False)
            | Q(product__effective_from__gt=F("generated_at"))
            | Q(product__effective_to__lte=F("generated_at"))
        ).count()

        if invalid:
            self.add_error(
                f"{invalid} recommendations contain unavailable products."
            )

    def add_error(self, message):
        self.errors.append(message)