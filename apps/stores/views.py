from django.shortcuts import render

# Create your views here.


from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.stores.models import Inventory
from apps.stores.serializers import InventoryListSerializer

class StoreInventoryViewSet(ReadOnlyModelViewSet):
    serializer_class = InventoryListSerializer

    def get_queryset(self):
        store_id = self.kwargs["store_id"]

        return (
            Inventory.objects
            .filter(store_id=store_id)
            .select_related(
                "product",
                "product__category",
            )
            .order_by("product__title")
        )
        