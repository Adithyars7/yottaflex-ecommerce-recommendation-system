from django.urls import path

from recommendations import views

urlpatterns = [
    path(
        "customers/<str:customer_id>/recommendations/",
        views.customer_recommendations,
        name="customer-recommendations",
    ),
]