import uuid

from django.db import models, transaction
from django.db.models import Q


class ProductRelation(models.Model):

    relation_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    source_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="outgoing_relations"
    )

    target_product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="incoming_relations"
    )

    relation_type = models.CharField(
        max_length=30,
        choices=[
            ("SIMILAR", "Similar"),
            ("FREQUENTLY_BOUGHT", "Frequently Bought Together"),
            ("COMPLEMENTARY", "Complementary"),
        ]
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0
    )

    effective_from = models.DateTimeField()

    effective_to = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_relations"

        constraints = [
            models.CheckConstraint(
                condition=~Q(source_product=models.F("target_product")),
                name="relation_products_different"
            ),
            models.CheckConstraint(
                condition=Q(score__gte=0) & Q(score__lte=1),
                name="relation_score_between_zero_one"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.relation_id:
            with transaction.atomic():
                self.relation_id = "TMP-" + uuid.uuid4().hex[:20]
                super().save(*args, **kwargs)

                self.relation_id = f"REL-{self.pk:06d}"
                super().save(update_fields=["relation_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.relation_id


class Recommendation(models.Model):

    recommendation_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="recommendations"
    )

    session = models.ForeignKey(
        "tracking.Session",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recommendations"
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="recommendations"
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=5
    )

    position = models.PositiveIntegerField()

    algorithm = models.CharField(
        max_length=100
    )

    generated_at = models.DateTimeField()

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "recommendations"

        indexes = [
            models.Index(
                fields=["customer", "generated_at"],
                name="rec_customer_time_idx"
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(score__gte=0) & Q(score__lte=1),
                name="recommendation_score_valid"
            ),
            models.CheckConstraint(
                condition=Q(position__gt=0),
                name="recommendation_position_positive"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.recommendation_id:
            with transaction.atomic():
                self.recommendation_id = "TMP-" + uuid.uuid4().hex[:20]
                super().save(*args, **kwargs)

                self.recommendation_id = f"REC-{self.pk:06d}"
                super().save(update_fields=["recommendation_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.recommendation_id