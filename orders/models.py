import uuid

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class Cart(models.Model):

    cart_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="carts"
    )

    session = models.ForeignKey(
        "tracking.Session",
        on_delete=models.PROTECT,
        related_name="carts",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("CONVERTED", "Converted"),
            ("ABANDONED", "Abandoned"),
        ],
        default="ACTIVE"
    )

    # Allows historical timestamps during synthetic data generation.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"

    def save(self, *args, **kwargs):

        if not self.cart_id:

            with transaction.atomic():

                self.cart_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                self.cart_id = (
                    f"CART-{self.created_at.year}-{self.pk:06d}"
                )

                super().save(update_fields=["cart_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.cart_id


class CartLine(models.Model):

    cart_line_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="lines"
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="cart_lines"
    )

    quantity = models.PositiveIntegerField(default=1)

    # Allows historical timestamps during synthetic data generation.
    added_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_lines"

        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="cart_line_quantity_positive"
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.cart_line_id:

            with transaction.atomic():

                self.cart_line_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                self.cart_line_id = f"CL-{self.pk:06d}"

                super().save(update_fields=["cart_line_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.cart_line_id


class Order(models.Model):

    order_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="orders"
    )

    cart = models.ForeignKey(
        Cart,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("CONFIRMED", "Confirmed"),
            ("SHIPPED", "Shipped"),
            ("DELIVERED", "Delivered"),
            ("CANCELLED", "Cancelled"),
        ],
        default="PENDING"
    )

    placed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"

    def save(self, *args, **kwargs):

        if not self.order_id:

            with transaction.atomic():

                self.order_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                self.order_id = (
                    f"ORD-{self.placed_at.year}-{self.pk:06d}"
                )

                super().save(update_fields=["order_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id


class OrderLine(models.Model):

    order_line_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="lines"
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    product_name_snapshot = models.CharField(max_length=255)

    class Meta:
        db_table = "order_lines"

        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_line_unit_price_nonnegative"
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.order_line_id:

            with transaction.atomic():

                self.order_line_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                self.order_line_id = f"OL-{self.pk:06d}"

                super().save(update_fields=["order_line_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.order_line_id