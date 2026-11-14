"""
Order models.

    User  1 ---< Order      (ForeignKey, CASCADE)
    Order 1 ---< OrderItem  (ForeignKey, CASCADE)
    Product 1 ---< OrderItem (ForeignKey, SET_NULL - history survives product deletion)
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    # Deleting a user removes their orders.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    shipping_name = models.CharField(max_length=150)
    shipping_address = models.TextField()
    phone = models.CharField(max_length=30)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"

    def get_absolute_url(self):
        return reverse("orders:order_detail", args=[self.pk])

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0"))


class OrderItem(models.Model):
    # Deleting an order removes its line items.
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Keep the line item if staff later delete the product.
    product = models.ForeignKey(
        "store.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    # Snapshots, so order history stays correct if the product changes.
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
