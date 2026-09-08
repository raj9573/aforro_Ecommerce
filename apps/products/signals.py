from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.products.models import Product
from apps.products.tasks import preprocess_product


@receiver(post_save, sender=Product)
def product_created(sender, instance, created, **kwargs):

    if created:
        preprocess_product.delay(instance.id)