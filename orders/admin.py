from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "shipping_name", "created_at")
    list_filter = ("status",)
    list_editable = ("status",)
    inlines = [OrderItemInline]
