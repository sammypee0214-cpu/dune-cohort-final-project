from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    # Read-only convenience field so API clients see the name, not just the id.
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
