from celery import shared_task


@shared_task
def send_order_confirmation(order_id):
    print(f"Order confirmation sent for Order ID: {order_id}")

    return f"Confirmation sent for order {order_id}"