"""
REST API for products (Django REST Framework).

    GET    /api/products/        -> 200 list
    POST   /api/products/        -> 201 created / 400 invalid   (staff auth)
    GET    /api/products/<id>/   -> 200 detail / 404 not found
    PUT    /api/products/<id>/   -> 200 updated                 (staff auth)
    PATCH  /api/products/<id>/   -> 200 updated                 (staff auth)
    DELETE /api/products/<id>/   -> 204 no content / 404        (staff auth)

Reads are public. Writes return 401 when not logged in and 403 when logged in
as a non-staff user.
"""
from rest_framework import generics

from .models import Product
from .permissions import IsStaffOrReadOnly
from .serializers import ProductSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
