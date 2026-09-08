from django.db import models

# Create your models here.

from apps.products.models import Product

class Store(models.Model):
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "product"],
                name="unique_store_product_inventory"
            )
        ]
    
    def __str__(self):
        return f"{self.store} - {self.product}"