from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory
from apps.orders.models import Order, OrderItem


class CategoryModelTest(TestCase):

    def test_category_creation(self):
        category = Category.objects.create(
            name="Electronics"
        )

        self.assertIsNotNone(category.id)
        self.assertEqual(category.name, "Electronics")

    def test_category_str(self):
        category = Category.objects.create(
            name="Electronics"
        )

        self.assertEqual(str(category), "Electronics")


class ProductModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics"
        )

    def test_product_creation(self):
        product = Product.objects.create(
            title="Laptop",
            description="Gaming laptop",
            price=Decimal("75000.00"),
            category=self.category
        )

        self.assertIsNotNone(product.id)
        self.assertEqual(product.title, "Laptop")
        self.assertEqual(product.description, "Gaming laptop")
        self.assertEqual(product.price, Decimal("75000.00"))
        self.assertEqual(product.category, self.category)

    def test_product_str(self):
        product = Product.objects.create(
            title="Laptop",
            description="Gaming laptop",
            price=Decimal("75000.00"),
            category=self.category
        )

        self.assertEqual(str(product), "Laptop")

    def test_category_product_relationship(self):
        Product.objects.create(
            title="Laptop",
            description="Gaming laptop",
            price=Decimal("75000.00"),
            category=self.category
        )

        Product.objects.create(
            title="Mouse",
            description="Wireless mouse",
            price=Decimal("1500.00"),
            category=self.category
        )

        self.assertEqual(self.category.products.count(), 2)


class StoreModelTest(TestCase):

    def test_store_creation(self):
        store = Store.objects.create(
            name="Main Store",
            location="Bangalore"
        )

        self.assertIsNotNone(store.id)
        self.assertEqual(store.name, "Main Store")
        self.assertEqual(store.location, "Bangalore")

    def test_store_str(self):
        store = Store.objects.create(
            name="Main Store",
            location="Bangalore"
        )

        self.assertEqual(str(store), "Main Store")


class InventoryModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics"
        )

        self.product = Product.objects.create(
            title="Laptop",
            description="Gaming laptop",
            price=Decimal("75000.00"),
            category=self.category
        )

        self.store = Store.objects.create(
            name="Main Store",
            location="Bangalore"
        )

    def test_inventory_creation(self):
        inventory = Inventory.objects.create(
            store=self.store,
            product=self.product,
            quantity=10
        )

        self.assertIsNotNone(inventory.id)
        self.assertEqual(inventory.store, self.store)
        self.assertEqual(inventory.product, self.product)
        self.assertEqual(inventory.quantity, 10)

    def test_inventory_str(self):
        inventory = Inventory.objects.create(
            store=self.store,
            product=self.product,
            quantity=10
        )

        self.assertEqual(
            str(inventory),
            f"{self.store} - {self.product}"
        )

    def test_unique_store_product_constraint(self):
        Inventory.objects.create(
            store=self.store,
            product=self.product,
            quantity=10
        )

        with self.assertRaises(IntegrityError):
            Inventory.objects.create(
                store=self.store,
                product=self.product,
                quantity=20
            )


class OrderModelTest(TestCase):

    def setUp(self):
        self.store = Store.objects.create(
            name="Main Store",
            location="Bangalore"
        )

    def test_order_creation(self):
        order = Order.objects.create(
            store=self.store
        )

        self.assertIsNotNone(order.id)
        self.assertEqual(order.store, self.store)

    def test_order_default_status(self):
        order = Order.objects.create(
            store=self.store
        )

        self.assertEqual(
            order.status,
            Order.Status.PENDING
        )

    def test_order_status_choices(self):
        order = Order.objects.create(
            store=self.store,
            status=Order.Status.CONFIRMED
        )

        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED
        )

    def test_order_str(self):
        order = Order.objects.create(
            store=self.store
        )

        self.assertEqual(
            str(order),
            f"Order {order.id}"
        )

    def test_order_created_at(self):
        order = Order.objects.create(
            store=self.store
        )

        self.assertIsNotNone(order.created_at)

    def test_store_orders_relationship(self):
        Order.objects.create(
            store=self.store
        )

        Order.objects.create(
            store=self.store
        )

        self.assertEqual(
            self.store.orders.count(),
            2
        )


class OrderItemModelTest(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics"
        )

        self.product = Product.objects.create(
            title="Laptop",
            description="Gaming laptop",
            price=Decimal("75000.00"),
            category=self.category
        )

        self.store = Store.objects.create(
            name="Main Store",
            location="Bangalore"
        )

        self.order = Order.objects.create(
            store=self.store
        )

    def test_order_item_creation(self):
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity_requested=3
        )

        self.assertIsNotNone(order_item.id)
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity_requested, 3)

    def test_order_item_str(self):
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity_requested=3
        )

        self.assertEqual(
            str(order_item),
            f"{self.product} - 3"
        )

    def test_order_items_relationship(self):
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity_requested=2
        )

        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity_requested=5
        )

        self.assertEqual(
            self.order.items.count(),
            2
        )

    def test_product_order_items_relationship(self):
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity_requested=2
        )

        self.assertEqual(
            self.product.order_items.count(),
            1
        )

