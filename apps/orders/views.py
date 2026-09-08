from django.shortcuts import render

# Create your views here.

from django.db import transaction
from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderResponseSerializer,
    
    OrderListSerializer
)
from apps.stores.models import (
    Inventory,
    Store
)

from django.db.models import Count
from apps.orders.tasks import send_order_confirmation



class CreateOrderView(APIView):
    @extend_schema(
        request=OrderCreateSerializer,
        responses={
            201: OrderResponseSerializer,
            400: dict,
        },
        summary="Create an order",
        description=(
            "Creates an order for a store. "
            "If all requested products have sufficient inventory, "
            "the order is CONFIRMED and stock is deducted. "
            "If any product has insufficient stock, "
            "the order is REJECTED and no stock is deducted."
        ),
    )
    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        store_id = validated_data["store_id"]
        items = validated_data["items"]


        with transaction.atomic():

            inventory_map = {}

            for item in items:

                product_id = item["product_id"]

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .filter(
                        store_id=store_id,
                        product_id=product_id,
                    )
                    .first()
                )

                inventory_map[product_id] = inventory


            insufficient_products = []

            for item in items:

                product_id = item["product_id"]
                requested_quantity = item["quantity_requested"]

                inventory = inventory_map[product_id]

                if (
                    inventory is None
                    or inventory.quantity < requested_quantity
                ):
                    insufficient_products.append(product_id)


            if insufficient_products:
                order_status = Order.Status.REJECTED
            else:
                order_status = Order.Status.CONFIRMED

            order = Order.objects.create(
                store_id=store_id,
                status=order_status,
            )


            for item in items:

                OrderItem.objects.create(
                    order=order,
                    product_id=item["product_id"],
                    quantity_requested=item["quantity_requested"],
                )


            if order_status == Order.Status.CONFIRMED:

                for item in items:

                    product_id = item["product_id"]
                    requested_quantity = item["quantity_requested"]

                    inventory = inventory_map[product_id]

                    inventory.quantity -= requested_quantity

                    inventory.save(
                        update_fields=["quantity"]
                    )
                
                transaction.on_commit(
                    lambda: send_order_confirmation.delay(order.id)
                )


        response_serializer = OrderResponseSerializer(order)

        return Response(
            {
                "status": "success",
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )



class StoreOrderViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OrderListSerializer

    def get_queryset(self):
        store_id = self.kwargs["store_id"]

        return (
            Order.objects
            .filter(store_id=store_id)
            .annotate(total_items=Count("items"))
            .order_by("-created_at")
        )