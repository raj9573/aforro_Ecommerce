from django.urls import path
from apps.orders.views import (
    CreateOrderView,
    StoreOrderViewSet
)
from rest_framework.routers import DefaultRouter 

router =  DefaultRouter()



urlpatterns = [
    path("orders/", CreateOrderView.as_view(), name="create-order"),
    
    
    path(
        "stores/<int:store_id>/orders/",
        StoreOrderViewSet.as_view({
                "get": "list",
                },
            name="store-orders",
        )
    ),
]