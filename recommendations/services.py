from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone

from catalog.models import Product
from tracking.models import PageView
from orders.models import Order, OrderLine, Cart, CartLine
from recommendations.models import ProductRelation, Recommendation


def get_available_products(as_of=None):
    """
    Return products available at the specified time.
    """

    if as_of is None:
        as_of = timezone.now()

    return Product.objects.filter(
        is_available=True,
        effective_from__lte=as_of,
    ).filter(
        models.Q(effective_to__isnull=True)
        | models.Q(effective_to__gt=as_of)
    )


def get_customer_activity(customer, as_of):
    """
    Retrieve customer activity at or before the recommendation time.
    """

    page_views = PageView.objects.filter(
        session__customer=customer,
        event_at__lte=as_of,
        session__started_at__lte=as_of,
    ).select_related("product", "session")

    orders = Order.objects.filter(
        customer=customer,
        placed_at__lte=as_of,
    )

    carts = Cart.objects.filter(
        customer=customer,
        created_at__lte=as_of,
    )

    cart_lines = CartLine.objects.filter(
        cart__in=carts,
        added_at__lte=as_of,
    ).select_related("product", "cart")

    order_lines = OrderLine.objects.filter(
        order__in=orders,
    ).select_related("product", "order")

    return {
        "page_views": page_views,
        "orders": orders,
        "order_lines": order_lines,
        "carts": carts,
        "cart_lines": cart_lines,
    }


def generate_recommendations(customer, as_of=None, limit=10):
    """
    Generate ranked product recommendations for a customer.
    """

    if as_of is None:
        as_of = timezone.now()

    activity = get_customer_activity(customer, as_of)

    available_products = get_available_products(as_of)

    available_product_ids = set(
        available_products.values_list("pk", flat=True)
    )

    scores = {}
    purchased_product_ids = set()

    # 1. Product views: 1 point.
    for page_view in activity["page_views"]:
        if page_view.product_id:
            product_id = page_view.product_id

            if product_id in available_product_ids:
                scores[product_id] = scores.get(product_id, 0) + 1

    # 2. Cart additions: 3 points.
    for cart_line in activity["cart_lines"]:
        product_id = cart_line.product_id

        if product_id in available_product_ids:
            scores[product_id] = scores.get(product_id, 0) + 3

    # 3. Purchases: 4 points.
    for order_line in activity["order_lines"]:
        product_id = order_line.product_id
        purchased_product_ids.add(product_id)

        if product_id in available_product_ids:
            scores[product_id] = scores.get(product_id, 0) + 4

    # 4. Related products.
    interacted_product_ids = set(scores.keys())

    relations = ProductRelation.objects.filter(
        source_product_id__in=interacted_product_ids,
        effective_from__lte=as_of,
    ).filter(
        models.Q(effective_to__isnull=True)
        | models.Q(effective_to__gt=as_of)
    )

    for relation in relations:
        target_id = relation.target_product_id

        if target_id in available_product_ids:
            scores[target_id] = (
                scores.get(target_id, 0)
                + float(relation.score) * 5
            )

    # 5. Exclude previously purchased products.
    for product_id in purchased_product_ids:
        scores.pop(product_id, None)

    # 6. Rank products by score.
    ranked_product_ids = sorted(
        scores,
        key=lambda product_id: scores[product_id],
        reverse=True,
    )

    products_by_id = {
        product.pk: product
        for product in available_products.filter(
            pk__in=ranked_product_ids
        )
    }

    recommendations = []

    for product_id in ranked_product_ids:
        if product_id in products_by_id:
            recommendations.append({
                "product": products_by_id[product_id],
                "score": scores[product_id],
            })

        if len(recommendations) >= limit:
            break

    return recommendations


@transaction.atomic
def save_recommendations(
    customer,
    session=None,
    as_of=None,
    limit=10,
):
    """
    Generate recommendations and save them to the database.

    Scores are normalized to the range 0 to 1.
    """

    if as_of is None:
        as_of = timezone.now()

    if session is not None and session.customer_id != customer.pk:
        raise ValueError(
            "The session must belong to the specified customer."
        )

    results = generate_recommendations(
        customer=customer,
        as_of=as_of,
        limit=limit,
    )

    if not results:
        return []

    max_score = max(item["score"] for item in results)

    saved_recommendations = []

    for position, item in enumerate(results, start=1):

        normalized_score = Decimal(
            str(round(item["score"] / max_score, 5))
        )

        recommendation = Recommendation.objects.create(
            customer=customer,
            session=session,
            product=item["product"],
            score=normalized_score,
            position=position,
            algorithm="rule_based_v1",
            generated_at=as_of,
            expires_at=as_of + timezone.timedelta(days=7),
        )

        saved_recommendations.append(recommendation)

    return saved_recommendations