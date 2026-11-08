from rest_framework import serializers

from catalog.models import Product
from recommendations.models import Recommendation


class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Product

        fields = [
            "product_id",
            "name",
            "description",
            "price",
            "category_name",
        ]


class RecommendationSerializer(serializers.ModelSerializer):

    product = ProductSerializer(read_only=True)

    class Meta:
        model = Recommendation

        fields = [
            "recommendation_id",
            "product",
            "score",
            "position",
            "algorithm",
            "generated_at",
            "expires_at",
        ]