from django.urls import path
from apps.search.views import (
    ProductSearchView,
    ProductSuggestView
)

urlpatterns = [
    path(
        "search/products/",
        ProductSearchView.as_view(),
        name="product-search",
    ),
    
    path(
        "search/suggest/",
        ProductSuggestView.as_view(),
        name="product-suggest",
    ),
]