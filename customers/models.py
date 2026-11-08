import uuid

from django.db import models, transaction


class Customer(models.Model):

    customer_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"

    def save(self, *args, **kwargs):

        if not self.customer_id:

            with transaction.atomic():

                self.customer_id = "T" + uuid.uuid4().hex[:19]

                super().save(*args, **kwargs)

                self.customer_id = f"CUS-{self.pk:06d}"

                super().save(update_fields=["customer_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_id