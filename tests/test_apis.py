from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory


# ============================================================
# TEST CACHE
# ============================================================

TEST_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "aforro-test-cache",
    }
}


# ============================================================
# BASE API TEST
# ============================================================

@override_settings(CACHES=TEST_CACHE)
class APITestBase(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Categories
        self.electronics = Category.objects.create(
            name="Electronics"
        )

        self.accessories = Category.objects.create(
            name="Accessories"
        )

        # Products
        self.laptop = Product.objects.create(
            title="Laptop",
            description="Powerful business laptop",
            price=Decimal("75000.00"),
            category=self.electronics,
        )

        self.mouse = Product.objects.create(
            title="Wireless Mouse",
            description="Wireless computer mouse",
            price=Decimal("1500.00"),
            category=self.accessories,
        )

        self.keyboard = Product.objects.create(
            title="Keyboard",
            description="Mechanical keyboard",
            price=Decimal("3000.00"),
            category=self.accessories,
        )

        # Stores
        self.store1 = Store.objects.create(
            name="Main Store",
            location="Bangalore",
        )

        self.store2 = Store.objects.create(
            name="Second Store",
            location="Chennai",
        )

        # Store 1 inventory
        Inventory.objects.create(
            store=self.store1,
            product=self.laptop,
            quantity=10,
        )

        Inventory.objects.create(
            store=self.store1,
            product=self.mouse,
            quantity=5,
        )

        Inventory.objects.create(
            store=self.store1,
            product=self.keyboard,
            quantity=0,
        )

        # Store 2 inventory
        Inventory.objects.create(
            store=self.store2,
            product=self.laptop,
            quantity=20,
        )


# ============================================================
# CREATE ORDER API
# ============================================================

class CreateOrderAPITest(APITestBase):

    @patch("apps.orders.views.send_order_confirmation.delay")
    def test_create_order_with_sufficient_inventory(self, mock_task):

        data = {
            "store_id": self.store1.id,
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

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get()

        self.assertEqual(
            order.store_id,
            self.store1.id,
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        inventory = Inventory.objects.get(
            store=self.store1,
            product=self.laptop,
        )

        self.assertEqual(
            inventory.quantity,
            8,
        )

        mock_task.assert_called_once_with(
            order.id
        )

    @patch("apps.orders.views.send_order_confirmation.delay")
    def test_create_order_with_insufficient_inventory(self, mock_task):

        data = {
            "store_id": self.store1.id,
            "items": [
                {
                    "product_id": self.keyboard.id,
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

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get()

        self.assertEqual(
            order.status,
            Order.Status.REJECTED,
        )

        inventory = Inventory.objects.get(
            store=self.store1,
            product=self.keyboard,
        )

        self.assertEqual(
            inventory.quantity,
            0,
        )

        mock_task.assert_not_called()

    def test_create_order_multiple_items(self):

        data = {
            "store_id": self.store1.id,
            "items": [
                {
                    "product_id": self.laptop.id,
                    "quantity_requested": 2,
                },
                {
                    "product_id": self.mouse.id,
                    "quantity_requested": 1,
                },
            ],
        }

        with self.captureOnCommitCallbacks(execute=True):

            response = self.client.post(
                "/api/orders/",
                data,
                format="json",
            )

        self.assertEqual(
            response.status_code,
            201,
        )

        order = Order.objects.get()

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )

        self.assertEqual(
            OrderItem.objects.filter(
                order=order
            ).count(),
            2,
        )

    def test_create_order_invalid_data(self):

        data = {
            "store_id": self.store1.id,
            "items": [],
        }

        response = self.client.post(
            "/api/orders/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_create_order_missing_store(self):

        data = {
            "items": [
                {
                    "product_id": self.laptop.id,
                    "quantity_requested": 1,
                }
            ],
        }

        response = self.client.post(
            "/api/orders/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )


# ============================================================
# STORE ORDERS API
# ============================================================

class StoreOrdersAPITest(APITestBase):

    def setUp(self):
        super().setUp()

        self.order1 = Order.objects.create(
            store=self.store1,
            status=Order.Status.CONFIRMED,
        )

        self.order2 = Order.objects.create(
            store=self.store1,
            status=Order.Status.REJECTED,
        )

        self.order3 = Order.objects.create(
            store=self.store2,
            status=Order.Status.CONFIRMED,
        )

        OrderItem.objects.create(
            order=self.order1,
            product=self.laptop,
            quantity_requested=2,
        )

        OrderItem.objects.create(
            order=self.order1,
            product=self.mouse,
            quantity_requested=1,
        )

        OrderItem.objects.create(
            order=self.order2,
            product=self.keyboard,
            quantity_requested=1,
        )

    def test_store_orders_list(self):

        response = self.client.get(
            f"/api/stores/{self.store1.id}/orders/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            2,
        )

    def test_store_orders_returns_only_selected_store_orders(self):

        response = self.client.get(
            f"/api/stores/{self.store1.id}/orders/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        returned_order_ids = {
            item["id"]
            for item in results
        }

        self.assertIn(
            self.order1.id,
            returned_order_ids,
        )

        self.assertIn(
            self.order2.id,
            returned_order_ids,
        )

        self.assertNotIn(
            self.order3.id,
            returned_order_ids,
        )

    def test_store_orders_invalid_store(self):

        response = self.client.get(
            "/api/stores/99999/orders/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )


# ============================================================
# STORE INVENTORY API
# ============================================================

class StoreInventoryAPITest(APITestBase):

    def test_store_inventory_list(self):

        response = self.client.get(
            f"/api/stores/{self.store1.id}/inventory/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            3,
        )

    def test_store_inventory_returns_only_selected_store(self):

        response = self.client.get(
            f"/api/stores/{self.store1.id}/inventory/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        # Check product titles instead of assuming
        # the serializer contains a "product" field.
        returned_titles = {
            item["product_title"]
            for item in results
        }

        self.assertIn(
            self.laptop.title,
            returned_titles,
        )

        self.assertIn(
            self.mouse.title,
            returned_titles,
        )

        self.assertIn(
            self.keyboard.title,
            returned_titles,
        )

    def test_store_inventory_ordered_by_product_title(self):

        response = self.client.get(
            f"/api/stores/{self.store1.id}/inventory/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        titles = [
            item["product_title"]
            for item in results
        ]

        self.assertEqual(
            titles,
            sorted(titles),
        )

    def test_store_inventory_invalid_store(self):

        response = self.client.get(
            "/api/stores/99999/inventory/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )


# ============================================================
# PRODUCT SEARCH API
# ============================================================

class ProductSearchAPITest(APITestBase):

    def test_product_search_by_title(self):

        response = self.client.get(
            "/api/search/products/?q=laptop"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["title"],
            "Laptop",
        )

    def test_product_search_by_description(self):

        response = self.client.get(
            "/api/search/products/?q=mechanical"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["title"],
            "Keyboard",
        )

    def test_product_search_by_category(self):

        response = self.client.get(
            "/api/search/products/?category=Accessories"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            2,
        )

    def test_product_search_min_price(self):

        response = self.client.get(
            "/api/search/products/?min_price=3000"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        for product in results:

            self.assertGreaterEqual(
                Decimal(str(product["price"])),
                Decimal("3000"),
            )

    def test_product_search_max_price(self):

        response = self.client.get(
            "/api/search/products/?max_price=3000"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        for product in results:

            self.assertLessEqual(
                Decimal(str(product["price"])),
                Decimal("3000"),
            )

    def test_product_search_store_filter(self):

        response = self.client.get(
            f"/api/search/products/?store_id={self.store1.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        product_ids = {
            item["id"]
            for item in results
        }

        self.assertIn(
            self.laptop.id,
            product_ids,
        )

        self.assertIn(
            self.mouse.id,
            product_ids,
        )

        self.assertIn(
            self.keyboard.id,
            product_ids,
        )

    def test_product_search_in_stock(self):

        response = self.client.get(
            f"/api/search/products/"
            f"?store_id={self.store1.id}"
            f"&in_stock=true"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        product_ids = {
            item["id"]
            for item in results
        }

        self.assertIn(
            self.laptop.id,
            product_ids,
        )

        self.assertIn(
            self.mouse.id,
            product_ids,
        )

        self.assertNotIn(
            self.keyboard.id,
            product_ids,
        )

    def test_product_search_out_of_stock(self):

        response = self.client.get(
            f"/api/search/products/"
            f"?store_id={self.store1.id}"
            f"&in_stock=false"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        product_ids = {
            item["id"]
            for item in results
        }

        self.assertIn(
            self.keyboard.id,
            product_ids,
        )

    def test_product_search_sort_by_price(self):

        response = self.client.get(
            "/api/search/products/?sort=price"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        prices = [
            Decimal(str(item["price"]))
            for item in results
        ]

        self.assertEqual(
            prices,
            sorted(prices),
        )

    def test_product_search_sort_by_newest(self):

        response = self.client.get(
            "/api/search/products/?sort=newest"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        ids = [
            item["id"]
            for item in results
        ]

        self.assertEqual(
            ids,
            sorted(ids, reverse=True),
        )

    def test_product_search_sort_by_relevance(self):

        response = self.client.get(
            "/api/search/products/?q=laptop&sort=relevance"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertGreaterEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["title"],
            "Laptop",
        )

    def test_product_search_combined_filters(self):

        response = self.client.get(
            f"/api/search/products/"
            f"?q=mouse"
            f"&category=Accessories"
            f"&min_price=1000"
            f"&max_price=2000"
            f"&store_id={self.store1.id}"
            f"&in_stock=true"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["title"],
            "Wireless Mouse",
        )

    def test_product_search_no_results(self):

        response = self.client.get(
            "/api/search/products/?q=nonexistent"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )


# ============================================================
# PRODUCT SUGGESTION API
# ============================================================

class ProductSuggestAPITest(APITestBase):

    def setUp(self):
        super().setUp()

        cache.clear()

    def tearDown(self):

        cache.clear()

        super().tearDown()

    def test_product_suggest_success(self):

        response = self.client.get(
            "/api/search/suggest/?q=lap"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertFalse(
            response.data["cached"]
        )

        self.assertGreaterEqual(
            len(response.data["results"]),
            1,
        )

    def test_product_suggest_requires_three_characters(self):

        response = self.client.get(
            "/api/search/suggest/?q=la"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_product_suggest_empty_keyword(self):

        response = self.client.get(
            "/api/search/suggest/?q="
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_product_suggest_case_insensitive(self):

        response = self.client.get(
            "/api/search/suggest/?q=LAP"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertGreaterEqual(
            len(response.data["results"]),
            1,
        )

    def test_product_suggest_cache(self):

        first_response = self.client.get(
            "/api/search/suggest/?q=lap"
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        self.assertFalse(
            first_response.data["cached"]
        )

        second_response = self.client.get(
            "/api/search/suggest/?q=lap"
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertTrue(
            second_response.data["cached"]
        )

    def test_product_suggest_returns_maximum_ten_results(self):

        for i in range(15):

            Product.objects.create(
                title=f"Laptop Model {i}",
                description="Laptop",
                price=Decimal("50000.00"),
                category=self.electronics,
            )

        cache.clear()

        response = self.client.get(
            "/api/search/suggest/?q=lap"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertLessEqual(
            len(response.data["results"]),
            10,
        )