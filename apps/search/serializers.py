from rest_framework import serializers
from apps.products.models import Product

class ProductSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    category_name = serializers.CharField(
        source="category.name"
    )
    quantity = serializers.IntegerField(
        allow_null=True,
        required=False
    )


class ProductSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        required=False,
        help_text="Search keyword"
    )
    category = serializers.CharField(
        required=False,
        help_text="Category name"
    )
    min_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2
    )
    max_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2
    )
    store_id = serializers.IntegerField(
        required=False
    )
    in_stock = serializers.BooleanField(
        required=False
    )
    sort = serializers.ChoiceField(
        required=False,
        choices=[
            ("price", "Price"),
            ("newest", "Newest"),
            ("relevance", "Relevance"),
        ]
    )
    

class ProductSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["title"]


class ProductSuggestResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    results = ProductSuggestSerializer(many=True)
    cached = serializers.BooleanField()