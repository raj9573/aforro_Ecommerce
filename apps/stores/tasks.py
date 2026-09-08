from celery import shared_task
from django.db.models import Sum, Count

from apps.stores.models import Inventory


@shared_task
def generate_inventory_summary():

    total_products = Inventory.objects.values(
        "product"
    ).distinct().count()

    total_quantity = Inventory.objects.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    out_of_stock = Inventory.objects.filter(
        quantity=0
    ).count()

    low_stock = Inventory.objects.filter(
        quantity__gt=0,
        quantity__lte=10
    ).count()

    store_summary = (
        Inventory.objects
        .values("store__name")
        .annotate(
            total_products=Count("product", distinct=True),
            total_quantity=Sum("quantity"),
        )
        .order_by("store__name")
    )

    print("========== DAILY INVENTORY SUMMARY ==========")
    print(f"Total Products: {total_products}")
    print(f"Total Quantity: {total_quantity}")
    print(f"Out of Stock: {out_of_stock}")
    print(f"Low Stock: {low_stock}")

    print("\nStore Summary:")

    for store in store_summary:
        print(
            f"{store['store__name']} - "
            f"Products: {store['total_products']}, "
            f"Quantity: {store['total_quantity']}"
        )

    print("=============================================")

    return "Inventory summary generated successfully"