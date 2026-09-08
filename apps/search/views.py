from django.db.models import (
    Q,
    OuterRef,
    Subquery,
    Case,
    When,
    IntegerField,
    Value
)

from rest_framework.generics import ListAPIView

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.products.models import Product
from apps.stores.models import Inventory
from apps.search.serializers import (
    ProductSearchSerializer,     
    ProductSuggestSerializer,
    ProductSuggestResponseSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from django.core.cache import cache
import hashlib
from apps.search.throttles import ProductSuggestRateThrottle

class ProductSearchView(ListAPIView):

    serializer_class = ProductSearchSerializer

    @extend_schema(
        summary="Search products",
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search product title, description or category",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by category name",
            ),
            OpenApiParameter(
                name="min_price",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Minimum price",
            ),
            OpenApiParameter(
                name="max_price",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum price",
            ),
            OpenApiParameter(
                name="store_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by store ID",
            ),
            OpenApiParameter(
                name="in_stock",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter products by stock availability",
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["price", "newest", "relevance"],
                description="Sort results",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    
    def get_queryset(self):

        queryset = Product.objects.select_related("category")

        keyword = self.request.query_params.get("q")

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(category__name__icontains=keyword)
            )

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category__name__iexact=category
            )

        min_price = self.request.query_params.get("min_price")

        if min_price:
            queryset = queryset.filter(
                price__gte=min_price
            )

        max_price = self.request.query_params.get("max_price")

        if max_price:
            queryset = queryset.filter(
                price__lte=max_price
            )

        store_id = self.request.query_params.get("store_id")

        if store_id:
            queryset = queryset.filter(
                inventory__store_id=store_id
            )

            inventory_quantity = (
                Inventory.objects
                .filter(
                    store_id=store_id,
                    product_id=OuterRef("pk"),
                )
                .values("quantity")[:1]
            )

            queryset = queryset.annotate(
                store_quantity=Subquery(
                    inventory_quantity
                )
            )

        in_stock = self.request.query_params.get("in_stock")

        if in_stock == "true":
            queryset = queryset.filter(
                inventory__quantity__gt=0
            )

        elif in_stock == "false":
            queryset = queryset.filter(
                inventory__quantity=0
            )

        sort = self.request.query_params.get("sort")

        if sort == "price":
            queryset = queryset.order_by("price")

        elif sort == "newest":
            queryset = queryset.order_by("-id")

        elif sort == "relevance" and keyword:
            queryset = queryset.annotate(
                relevance=Case(
                    When(title__iexact=keyword, then=4),
                    When(title__icontains=keyword, then=3),
                    When(description__icontains=keyword, then=2),
                    When(category__name__icontains=keyword, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ).order_by("-relevance", "title")

        else:
            queryset = queryset.order_by("title")

        return queryset
    


from apps.products.models import Product

class ProductSuggestView(APIView):
    
    throttle_classes = [ProductSuggestRateThrottle]

    @extend_schema(
        summary="Product autocomplete suggestions",
        description=(
            "Returns up to 10 product titles matching the search keyword. "
            "Prefix matches are ranked before general matches. "
            "Minimum 3 characters are required."
        ),
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Search keyword. Minimum 3 characters.",
            ),
        ],
        responses=ProductSuggestResponseSerializer,
    )
    def get(self, request):

        keyword = request.query_params.get("q", "").strip().lower()

        if len(keyword) < 3:
            return Response(
                {
                    "status": "error",
                    "message": "Search keyword must contain at least 3 characters.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        keyword_hash = hashlib.md5(
            keyword.encode("utf-8")
        ).hexdigest()
        cache_key = f"product_suggest:{keyword_hash}"

        cached_results = cache.get(cache_key)

        if cached_results is not None:
            response_data = {
                "status": "success",
                "results": cached_results,
                "cached":True
            }

            response_serializer = ProductSuggestResponseSerializer(
                response_data
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        products = (
            Product.objects
            .filter(title__icontains=keyword)
            .annotate(
                match_priority=Case(
                    When(
                        title__istartswith=keyword,
                        then=Value(1),
                    ),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by(
                "match_priority",
                "title",
            )[:10]
        )

        product_serializer = ProductSuggestSerializer(
            products,
            many=True,
        )

        results = product_serializer.data

        cache.set(
            cache_key,
            results,
            timeout=300,
        )

        response_data = {
            "status": "success",
            "results": results,
            "cached":False
        }

        response_serializer = ProductSuggestResponseSerializer(
            response_data
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )