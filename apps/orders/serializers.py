from rest_framework import serializers

from apps.products.models import Product
from apps.stores.models import Store
from apps.orders.models import Order, OrderItem


class OrderItemRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity_requested = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Product does not exist."
            )
        return value


class OrderCreateSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = OrderItemRequestSerializer(many=True)

    def validate_store_id(self, value):
        if not Store.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Store does not exist."
            )
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one item is required."
            )

        product_ids = [item["product_id"] for item in value]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products are not allowed."
            )

        return value


class OrderItemResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = [
            "product",
            "quantity_requested",
        ]


class OrderResponseSerializer(serializers.ModelSerializer):

    items = OrderItemResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "store",
            "status",
            "created_at",
            "items",
        ]

class OrderListSerializer(serializers.ModelSerializer):
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "created_at",
            "total_items",
        ]
        