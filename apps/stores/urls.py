from django.urls import path
from apps.stores.views import StoreInventoryViewSet


urlpatterns = [
    path(
        "stores/<int:store_id>/inventory/",
        StoreInventoryViewSet.as_view({
            "get": "list",
        }),
        name="store-inventory",
    ),
]