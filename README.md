# Aforro Backend Developer Assignment

A Django REST API backend demonstrating REST API design, database modeling, query optimization, asynchronous processing with Celery, Redis caching, rate limiting, and containerized development.

## Tech Stack

* Python
* Django
* Django REST Framework
* SQLite
* Redis
* Celery
* Docker
* Docker Compose
* drf-spectacular / Swagger

---

## Project Structure

```text
aforro_backend/
│
├── manage.py
├── settings.py
├── urls.py
├── celery_app.py
│
├── apps/
│   ├── products/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── signals.py
│   │   ├── tasks.py
│   │   └── ...
│   │
│   ├── stores/
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── tasks.py
│   │   └── ...
│   │
│   ├── orders/
│   │   ├── models.py
│   │   ├── tasks.py
│   │   └── ...
│   │
│   └── search/
│       ├── serializers.py
│       ├── throttles.py
│       ├── urls.py
│       ├── views.py
│       └── ...
│
└── requirements.txt
```

---

# 1. Features

The project implements the following backend functionality:

* Product and category management
* Store and inventory management
* Order and order-item management
* Product search API
* Product suggestion API
* Search filtering and sorting
* Inventory availability filtering
* Query optimization
* Redis caching
* API rate limiting
* Celery asynchronous tasks
* Celery Beat periodic tasks
* Automatic product preprocessing
* Asynchronous order confirmation
* Daily inventory reporting
* Django Admin
* Swagger API documentation
* Docker support

---

# 2. Data Models

## Category

Stores product categories.

```text
Category
---------
id
name
```

## Product

Stores product information.

```text
Product
-------
id
title
description
search_text
price
category
```

`search_text` is populated asynchronously when a product is created.

## Store

Stores store information.

```text
Store
-----
id
name
location
```

## Inventory

Maintains the quantity of each product available in each store.

```text
Inventory
---------
id
store
product
quantity
```

A unique constraint is applied to prevent duplicate `store + product` inventory records.

## Order

Stores customer orders.

```text
Order
-----
id
store
status
created_at
```

Possible statuses:

```text
PENDING
CONFIRMED
REJECTED
```

## OrderItem

Stores products requested in an order.

```text
OrderItem
---------
id
order
product
quantity_requested
```

---

# 3. API Documentation

Swagger documentation is available at:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

Swagger provides an interactive interface for testing the APIs.

---

# 4. Product Search

The product search API supports:

* Keyword search
* Category filtering
* Minimum price
* Maximum price
* Store filtering
* In-stock filtering
* Sorting
* Pagination
* Search relevance

Example:

```text
GET /api/search/?q=phone
```

Example with filters:

```text
GET http://127.0.0.1:8000/api/search/products/?q=phone&category=Electronics&min_price=500&max_price=50000&in_stock=true
```

Search results are ordered based on relevance where applicable.

---

# 5. Product Suggestions

The suggestion API provides product title suggestions.

Endpoint:

```text
GET /api/search/suggest/?q=pho
```

The API requires a minimum of 3 characters.

Prefix matches are given higher priority than general matches.

Example response:

```json
{
    "status": "success",
    "results": [
        {
            "title": "Phone"
        },
        {
            "title": "Phone Cover"
        }
    ]
}
```

The result is limited to 10 suggestions.

---

# 6. Redis Caching

Redis is used for caching product suggestions.

Cache configuration:

```text
redis://127.0.0.1:6379/1
```

Suggestion results are cached for 5 minutes.

```python
cache.set(cache_key, results, timeout=300)
```

The keyword is hashed before creating the cache key.

Example logical cache key:

```text
product_suggest:<md5_hash>
```

This reduces repeated database queries for frequently searched keywords.

---

# 7. Rate Limiting

The product suggestion API is protected using Django REST Framework throttling.

Limit:

```text
20 requests per minute per IP
```

Configuration:

```python
"DEFAULT_THROTTLE_RATES": {
    "product_suggest": "20/min",
}
```

The throttle is applied only to:

```text
GET /api/search/suggest/
```

When the limit is exceeded, the API returns:

```text
HTTP 429 Too Many Requests
```

---

# 8. Celery + Redis

Celery is used for asynchronous/background processing.

Redis is used as the Celery broker and result backend.

```text
redis://127.0.0.1:6379/2
```

The project includes the following asynchronous tasks:

### 8.1 Order Confirmation

When an order is confirmed, an asynchronous Celery task is triggered.

```python
send_order_confirmation.delay(order.id)
```

The task:

```text
Order confirmed
      ↓
Celery task triggered
      ↓
Redis broker
      ↓
Celery worker
      ↓
Order confirmation processed
```

The task is triggered after the database transaction is successfully committed.

---

# 9. Automatic Product Preprocessing

Products are created through Django Admin.

When a new product is created, a Django `post_save` signal triggers a Celery task.

Flow:

```text
Django Admin
     ↓
Create Product
     ↓
post_save signal
     ↓
preprocess_product.delay(product.id)
     ↓
Redis
     ↓
Celery Worker
     ↓
Normalize title + description
     ↓
Update search_text
     ↓
Database
```

The task creates normalized search text from the product title and description.

Example:

```text
Title:
"  Wireless Headphones  "

Description:
"Bluetooth Noise Cancelling Headphones"
```

Stored `search_text`:

```text
wireless headphones bluetooth noise cancelling headphones
```

This preprocessing is performed asynchronously so the main product creation flow is not blocked.

---

# 10. Inventory Reports

Celery Beat is used for periodic inventory reporting.

The inventory report calculates:

* Total products
* Total inventory quantity
* Out-of-stock products
* Low-stock products
* Store-level inventory summary

Low stock is currently defined as:

```text
quantity > 0 and quantity <= 10
```

Celery Beat is configured to run the inventory summary periodically.

For testing, the schedule can be configured to run every minute:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "generate-inventory-summary-every-minute": {
        "task": "apps.stores.tasks.generate_inventory_summary",
        "schedule": crontab(minute="*"),
    },
}
```

For the actual daily requirement:

```python
CELERY_BEAT_SCHEDULE = {
    "generate-daily-inventory-summary": {
        "task": "apps.stores.tasks.generate_inventory_summary",
        "schedule": crontab(hour=23, minute=59),
    },
}
```

---

# 11. Running Celery

Start the Django development server:

```bash
python manage.py runserver
```

Start the Celery worker in another terminal:

```bash
celery -A aforro_backend.celery:app worker --loglevel=info --pool=solo
```

Start Celery Beat in another terminal:

```bash
celery -A aforro_backend.celery:app beat --loglevel=info
```

For the inventory report, both the Celery worker and Celery Beat need to be running.

---

# 12. Testing Rate Limiting

The suggestion endpoint can be tested using Python:

```python
import requests

url = "http://127.0.0.1:8000/api/search/suggest/?q=adaptive"

for i in range(1, 30):
    response = requests.get(url)
    print(i, response.status_code)
```

Expected behavior:

```text
Requests 1-20  → 200
Requests 21+   → 429
```

The exact request at which `429` appears can vary if previous requests from the same IP are still inside the one-minute throttle window.

---

# 13. Database Query Optimization

The project uses Django ORM to optimize database access.

Examples include:

* `select_related()`
* Aggregations
* Conditional expressions
* Filtering at database level
* Pagination
* Avoiding unnecessary queries
* Database constraints

For example, related foreign-key data can be fetched using:

```python
select_related("category")
```

This helps avoid unnecessary database queries when accessing related objects.

---

# 14. Pagination

Django REST Framework pagination is enabled globally.

Default page size:

```text
20
```

Example:

```text
GET /api/search/?q=phone&page=2
```

This prevents large result sets from being returned in a single response.

---

# 15. Docker

The project is designed to run using Docker and Docker Compose.

The expected services are:

```text
Django Web
   ↓
SQLite3
Redis
Celery Worker
```

Docker Compose can be used to start the required services.

Example:

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker compose ps
```

Stop services:

```bash
docker compose down
```

---

# 16. Local Setup

Clone the repository:

```bash
git clone <repository-url>
cd aforro_backend
```

Create and activate a virtual environment:

```bash
python -m venv env
```

Windows:

```bash
env\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Start Django:

```bash
python manage.py runserver
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

Swagger:

```text
http://127.0.0.1:8000/api/docs/
```

---

# 17. Environment Variables

Sensitive configuration such as database credentials and other secrets should be stored in environment variables rather than committed to Git.

Example:

```text
REDIS_HOST=
REDIS_PORT=
```

A `.env` file should not be committed to the repository.

Add it to `.gitignore`:

```text
.env
```

---

# 18. Architecture Overview

```text
                         Client
                           |
                           v
                    Django REST API
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
       Product          Search            Orders
          |                |                |
          |                v                |
          |             Redis Cache         |
          |                                 |
          +-------------+-------------------+
                        |
                        v
                    SQLite3
                        
Celery Flow:

Django
   |
   v
Redis Broker
   |
   v
Celery Worker
   |
   v
Background Tasks


Periodic Tasks:

Celery Beat
    |
    v
Redis
    |
    v
Celery Worker
    |
    v
Inventory Report
```

---

# 19. Key Design Decisions

### Asynchronous Processing

Celery is used for operations that do not need to block the main request flow, such as:

* Order confirmation
* Product preprocessing
* Inventory reporting

### Redis

Redis is used separately for:

* Django application caching
* Celery message broker/result backend
* API throttling state

Different Redis databases are used to keep these concerns separated.

```text
DB 1 → Django cache / throttling
DB 2 → Celery
```

### Signals

Django signals are used to automatically trigger product preprocessing when a new product is created.

### Celery Beat

Celery Beat is used for periodic tasks such as inventory reports.

---

# 20. API Error Handling

The APIs return appropriate HTTP status codes for common scenarios.

Examples:

```text
200 OK
201 Created
400 Bad Request
404 Not Found
429 Too Many Requests
```

Validation is handled using Django REST Framework serializers.

---

# 21. Testing

The APIs can be tested using:

* Swagger UI
* Postman
* Python `requests`
* Django Admin

Swagger is recommended for quickly testing the available API endpoints.

---

# 22. Future Improvements

Possible improvements include:

* Automated unit and integration tests
* JWT authentication
* Redis distributed caching improvements
* Full-text search using SQLite3
* Elasticsearch/OpenSearch for large-scale search
* Persistent inventory report history
* Email service integration for order confirmation
* CI/CD pipeline
* Production deployment using Docker

---

## Conclusion

This project demonstrates a complete Django backend module covering:

```text
REST APIs
   +
Database Modeling
   +
Query Optimization
   +
Redis Caching
   +
Rate Limiting
   +
Celery
   +
Celery Beat
   +
Django Signals
   +
SQLite3
   +
Docker
   +
Swagger
```

The implementation focuses on clean separation of responsibilities, asynchronous processing, efficient database access, and production-oriented backend practices.
