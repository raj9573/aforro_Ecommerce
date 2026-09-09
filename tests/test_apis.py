from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory


TEST_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aforro-test-cache",
    }
}


@override_settings(CACHES=TEST_CACHE)
class OrderAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            name="Electronics"
        )

        self.laptop = Product.objects.create(
            title="Laptop",
            description="Business laptop",
            price=Decimal("75000.00"),
            category=self.category,
        )

        self.store = Store.objects.create(
            name="Main Store",
            location="Bangalore",
        )

        Inventory.objects.create(
            store=self.store,
            product=self.laptop,
            quantity=10,
        )

    @patch("apps.orders.views.send_order_confirmation.delay")
    def test_create_order_with_sufficient_inventory(self, mock_task):

        data = {
            "store_id": self.store.id,
            "items": [
                {
                    "product_id": self.laptop.id,
                    "quantity_requested": 2,
                }
            ],
        }

        with self.captureOnCommitCallbacks(execute=True):

            response = self.client.post(
                "/api/orders/",
                data,
                format="json",
            )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        inventory = Inventory.objects.get(
            store=self.store,
            product=self.laptop,
        )

        self.assertEqual(
            inventory.quantity,
            8,
        )

        mock_task.assert_called_once_with(order.id)

    @patch("apps.orders.views.send_order_confirmation.delay")
    def test_create_order_with_insufficient_inventory(self, mock_task):

        data = {
            "store_id": self.store.id,
            "items": [
                {
                    "product_id": self.laptop.id,
                    "quantity_requested": 20,
                }
            ],
        }

        with self.captureOnCommitCallbacks(execute=True):

            response = self.client.post(
                "/api/orders/",
                data,
                format="json",
            )

        self.assertEqual(response.status_code, 201)

        order = Order.objects.get()

        self.assertEqual(
            order.status,
            Order.Status.REJECTED,
        )

        inventory = Inventory.objects.get(
            store=self.store,
            product=self.laptop,
        )

        self.assertEqual(
            inventory.quantity,
            10,
        )

        mock_task.assert_not_called()