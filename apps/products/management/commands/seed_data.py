from decimal import Decimal
from random import randint, sample

from django.core.management.base import BaseCommand
from faker import Faker

from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory


class Command(BaseCommand):
    help = "Generate dummy categories, products, stores and inventory data"

    def handle(self, *args, **options):
        fake = Faker()

       
        CATEGORY_COUNT = 15
        PRODUCT_COUNT = 1200
        STORE_COUNT = 25
        PRODUCTS_PER_STORE = 300

       
        self.stdout.write("Clearing existing data...")

        Inventory.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Store.objects.all().delete()


        self.stdout.write("Creating categories...")

        category_names = [
            "Electronics",
            "Clothing",
            "Footwear",
            "Home Appliances",
            "Furniture",
            "Books",
            "Groceries",
            "Beauty",
            "Sports",
            "Toys",
            "Accessories",
            "Stationery",
            "Kitchen",
            "Automotive",
            "Health",
        ]

        categories = [
            Category(name=name)
            for name in category_names[:CATEGORY_COUNT]
        ]

        Category.objects.bulk_create(categories)

        categories = list(Category.objects.all())




        self.stdout.write("Creating products...")

        products = []

        for i in range(PRODUCT_COUNT):
            products.append(
                Product(
                    title=fake.unique.catch_phrase(),
                    description=fake.text(max_nb_chars=200),
                    price=Decimal(
                        f"{randint(100, 100000) / 100:.2f}"
                    ),
                    category=categories[i % len(categories)],
                )
            )

        Product.objects.bulk_create(
            products,
            batch_size=500,
        )

        products = list(Product.objects.all())



        self.stdout.write("Creating stores...")

        stores = []

        for i in range(STORE_COUNT):
            stores.append(
                Store(
                    name=f"Store {i + 1} - {fake.city()}",
                    location=fake.address(),
                )
            )

        Store.objects.bulk_create(stores)

        stores = list(Store.objects.all())




        self.stdout.write("Creating inventory...")

        inventory = []

        for store in stores:

            store_products = sample(
                products,
                PRODUCTS_PER_STORE,
            )

            for product in store_products:
                inventory.append(
                    Inventory(
                        store=store,
                        product=product,
                        quantity=randint(0, 100),
                    )
                )

        Inventory.objects.bulk_create(
            inventory,
            batch_size=1000,
        )

        
        
        
        self.stdout.write(
            self.style.SUCCESS(
                "\nSeed data created successfully!"
            )
        )

        self.stdout.write(
            f"Categories : {Category.objects.count()}"
        )

        self.stdout.write(
            f"Products   : {Product.objects.count()}"
        )

        self.stdout.write(
            f"Stores     : {Store.objects.count()}"
        )

        self.stdout.write(
            f"Inventory  : {Inventory.objects.count()}"
        )