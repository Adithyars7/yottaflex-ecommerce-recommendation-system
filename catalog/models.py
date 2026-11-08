
import uuid

from django.db import models, transaction


class Category(models.Model):

    category_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"

    def save(self, *args, **kwargs):
        if not self.category_id:
            with transaction.atomic():
                self.category_id = "T" + uuid.uuid4().hex[:19]
                super().save(*args, **kwargs)

                self.category_id = f"CAT-{self.pk:06d}"
                super().save(update_fields=["category_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):

    product_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_available = models.BooleanField(default=True)
    effective_from = models.DateTimeField()

    effective_to = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"

    def save(self, *args, **kwargs):
        if not self.product_id:
            with transaction.atomic():
                self.product_id = "T" + uuid.uuid4().hex[:19]
                super().save(*args, **kwargs)

                self.product_id = f"SKU-{self.pk:06d}"
                super().save(update_fields=["product_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.product_id