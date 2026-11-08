from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from customers.models import Customer
from tracking.models import Session

from recommendations.services import save_recommendations
from recommendations.serializers import RecommendationSerializer


@api_view(["GET"])
def customer_recommendations(request, customer_id):

    # Find the customer using their customer ID.
    customer = get_object_or_404(
        Customer,
        customer_id=customer_id,
    )

    # Read the requested recommendation limit.
    try:
        limit = int(request.query_params.get("limit", 10))
    except (TypeError, ValueError):
        return Response(
            {"error": "Limit must be a valid integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if limit < 1 or limit > 50:
        return Response(
            {"error": "Limit must be between 1 and 50."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Optionally accept a session ID.
    session = None
    session_id = request.query_params.get("session_id")

    if session_id:
        session = get_object_or_404(
            Session,
            session_id=session_id,
            customer=customer,
        )

    # Generate and save recommendations.
    recommendations = save_recommendations(
        customer=customer,
        session=session,
        limit=limit,
    )

    # Convert recommendations into JSON.
    serializer = RecommendationSerializer(
        recommendations,
        many=True,
    )

    return Response(
        {
            "customer_id": customer.customer_id,
            "total_recommendations": len(recommendations),
            "recommendations": serializer.data,
        },
        status=status.HTTP_200_OK,
    )