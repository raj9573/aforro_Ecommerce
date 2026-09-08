from celery import shared_task

from apps.products.models import Product


@shared_task
def preprocess_product(product_id):
    product = Product.objects.get(id=product_id)

    normalized_title = product.title.strip().lower()
    normalized_description = product.description.strip().lower()

    print(f"Processing Product ID: {product_id}")
    print(f"Title: {normalized_title}")
    print(f"Description: {normalized_description}")
    
    
    product.title = normalized_title 
    product.description = normalized_description
    product.save(
        update_fields=["title", "description"]
    )


    return f"Product {product_id} processed successfully"