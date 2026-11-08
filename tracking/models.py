import uuid

from django.db import models, transaction
from django.db.models import Q


class Session(models.Model):

    session_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    started_at = models.DateTimeField()

    ended_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("COMPLETED", "Completed"),
            ("EXPIRED", "Expired"),
        ],
        default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sessions"

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(ended_at__isnull=True) |
                    Q(ended_at__gte=models.F("started_at"))
                ),
                name="session_end_after_start"
            )
        ]

    def save(self, *args, **kwargs):

        if not self.session_id:

            with transaction.atomic():

                self.session_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                self.session_id = (
                    f"SES-{self.started_at.year}-{self.pk:06d}"
                )

                super().save(update_fields=["session_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.session_id


class PageView(models.Model):

    event_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.PROTECT,
        related_name="page_views"
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="page_views"
    )

    page_type = models.CharField(
        max_length=30,
        choices=[
            ("HOME", "Home"),
            ("PRODUCT", "Product"),
            ("CATEGORY", "Category"),
            ("CART", "Cart"),
            ("CHECKOUT", "Checkout"),
        ]
    )

    page_url = models.CharField(
        max_length=500,
        blank=True
    )

    event_at = models.DateTimeField()

    recorded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "page_views"

        indexes = [
            models.Index(
                fields=["session", "event_at"],
                name="page_session_time_idx"
            ),
            models.Index(
                fields=["product", "event_at"],
                name="page_product_time_idx"
            ),
        ]

        ordering = ["event_at"]

    def save(self, *args, **kwargs):

        if not self.event_id:

            with transaction.atomic():

                # Lock the parent session to prevent concurrent
                # event creation from using the same sequence.
                locked_session = (
                    Session.objects
                    .select_for_update()
                    .get(pk=self.session_id)
                )

                # Temporary unique ID allows us to save the row
                # and obtain its database primary key.
                self.event_id = (
                    "TMP-" + uuid.uuid4().hex[:20]
                )

                super().save(*args, **kwargs)

                # Find existing event numbers for this session.
                prefix = f"EVT-{locked_session.session_id}-"

                existing_ids = (
                    PageView.objects
                    .filter(event_id__startswith=prefix)
                    .exclude(pk=self.pk)
                    .values_list("event_id", flat=True)
                )

                sequence_numbers = []

                for existing_id in existing_ids:

                    try:
                        sequence = int(
                            existing_id.rsplit("-", 1)[1]
                        )

                        sequence_numbers.append(sequence)

                    except (ValueError, IndexError):
                        continue

                next_sequence = (
                    max(sequence_numbers, default=0) + 1
                )

                # Generate the final event ID.
                self.event_id = (
                    f"{prefix}{next_sequence:03d}"
                )

                super().save(update_fields=["event_id"])

        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.event_id