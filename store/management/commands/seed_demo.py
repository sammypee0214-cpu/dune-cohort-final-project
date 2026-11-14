"""Idempotent starter catalogue so the live site and API have something to show."""
from django.core.management.base import BaseCommand

from store.models import Category, Product

CATALOGUE = {
    "Electronics": [
        ("Wireless Headphones", "Over-ear Bluetooth headphones with 30 hour battery.", "59.99", 25),
        ("Portable Power Bank", "10,000 mAh fast-charging power bank.", "24.50", 40),
    ],
    "Fashion": [
        ("Classic Denim Jacket", "Mid-weight denim jacket, unisex fit.", "49.00", 15),
        ("Canvas Backpack", "Water-resistant 20L everyday backpack.", "34.99", 30),
    ],
    "Home & Kitchen": [
        ("Ceramic Coffee Mug Set", "Set of four 350 ml stoneware mugs.", "19.99", 50),
        ("Stainless Steel Bottle", "Insulated 750 ml bottle, keeps drinks cold for 24 hours.", "17.25", 60),
    ],
    "Books": [
        ("Learning Python", "A practical introduction to Python programming.", "29.90", 20),
        ("Django for Beginners", "Build web apps step by step with Django.", "27.00", 20),
    ],
}


class Command(BaseCommand):
    help = "Create demo categories and products (safe to run repeatedly)."

    def handle(self, *args, **options):
        new_products = 0
        for category_name, products in CATALOGUE.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock in products:
                _, created = Product.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={"description": description, "price": price, "stock": stock},
                )
                new_products += created
        self.stdout.write(self.style.SUCCESS(f"Seed complete: {new_products} new products."))
