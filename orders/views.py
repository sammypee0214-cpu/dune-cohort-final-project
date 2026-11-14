"""Cart, checkout and order history."""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def _parse_quantity(raw, default=1):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    items = Cart(request).items()
    total = sum((row["line_total"] for row in items), Decimal("0"))
    return render(request, "orders/cart.html", {"items": items, "total": total})


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.in_stock:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect(product)
    quantity = max(_parse_quantity(request.POST.get("quantity")), 1)
    Cart(request).add(product, quantity)
    messages.success(request, f"{product.name} added to your cart.")
    return redirect("orders:cart")


@require_POST
def cart_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = _parse_quantity(request.POST.get("quantity"), default=1)
    Cart(request).set_quantity(product, quantity)
    messages.success(request, "Cart updated.")
    return redirect("orders:cart")


@require_POST
def cart_remove(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Cart(request).remove(product)
    messages.success(request, f"{product.name} removed from your cart.")
    return redirect("orders:cart")


@login_required
def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("store:product_list")

    total = sum((row["line_total"] for row in items), Decimal("0"))

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # One transaction: either the whole order is saved and stock is
            # reduced, or nothing changes.
            with transaction.atomic():
                ids = [row["product"].pk for row in items]
                locked = {
                    p.pk: p
                    for p in Product.objects.select_for_update().filter(pk__in=ids)
                }
                for row in items:
                    product = locked[row["product"].pk]
                    if product.stock < row["quantity"]:
                        messages.error(
                            request,
                            f"Only {product.stock} of {product.name} left in stock. "
                            "Please update your cart.",
                        )
                        return redirect("orders:cart")

                order = form.save(commit=False)
                order.user = request.user
                order.save()
                for row in items:
                    product = locked[row["product"].pk]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=row["quantity"],
                    )
                    product.stock -= row["quantity"]
                    product.save(update_fields=["stock"])

            cart.clear()
            messages.success(request, f"Thank you! Order #{order.pk} has been placed.")
            return redirect(order)  # redirect after POST
    else:
        form = CheckoutForm(initial={"shipping_name": request.user.get_full_name()})

    return render(
        request, "orders/checkout.html", {"form": form, "items": items, "total": total}
    )


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    """Customers see their own orders. Staff can see any order."""
    queryset = Order.objects.prefetch_related("items")
    if not request.user.is_staff:
        queryset = queryset.filter(user=request.user)
    order = get_object_or_404(queryset, pk=pk)
    return render(request, "orders/order_detail.html", {"order": order})
