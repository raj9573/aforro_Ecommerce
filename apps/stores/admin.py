from django.contrib import admin

from apps.stores.models import Store, Inventory


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "location",
    ]

    search_fields = [
        "name",
        "location",
    ]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product_id",
        "product",
        "store",
        "store_location",
        "quantity",
    ]

    list_filter = [
        "store",
        "product",
    ]

    search_fields = [
        "product__title",
        "store__name",
        "store__location",
    ]

    ordering = [
        "product_id",
    ]

    @admin.display(description="Product ID")
    def product_id(self, obj):
        return obj.product_id

    @admin.display(description="Store Location")
    def store_location(self, obj):
        return obj.store.location