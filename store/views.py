"""Storefront pages and staff-only product management."""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import staff_required
from .forms import ProductForm
from .models import Category, Product


def product_list(request):
    """Home page: all products with optional search and category filter."""
    products = Product.objects.select_related("category")

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "")

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    context = {
        "products": products,
        "categories": Category.objects.all(),
        "query": query,
        "selected_category": category_slug,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, pk):
    """Single product page (dynamic URL: /products/<pk>/)."""
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    related = Product.objects.filter(category=product.category).exclude(pk=pk)[:4]
    return render(
        request, "store/product_detail.html", {"product": product, "related": related}
    )


def category_detail(request, slug):
    """Products in one category (dynamic URL: /category/<slug>/)."""
    category = get_object_or_404(Category, slug=slug)
    return render(
        request,
        "store/category_detail.html",
        {"category": category, "products": category.products.all()},
    )


@staff_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" was added to the store.')
            return redirect(product)  # redirect after POST
    else:
        form = ProductForm()
    return render(
        request, "store/product_form.html", {"form": form, "heading": "Add a product"}
    )


@staff_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" was updated.')
            return redirect(product)
    else:
        form = ProductForm(instance=product)
    return render(
        request,
        "store/product_form.html",
        {"form": form, "heading": f"Edit {product.name}", "product": product},
    )


@staff_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" was deleted.')
        return redirect("store:product_list")
    return render(request, "store/product_confirm_delete.html", {"product": product})
