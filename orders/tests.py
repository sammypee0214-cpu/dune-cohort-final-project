from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product

from .models import Order, OrderItem


class OrderTestCase(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Books")
        self.product = Product.objects.create(
            category=category, name="Python Book", price="10.00", stock=5
        )
        self.user = User.objects.create_user("sam", password="pass12345")
        self.other = User.objects.create_user("eve", password="pass12345")

    def add_to_cart(self, quantity=2):
        return self.client.post(
            reverse("orders:cart_add", args=[self.product.pk]), {"quantity": quantity}
        )

    checkout_data = {
        "shipping_name": "Sam Doe",
        "shipping_address": "1 Main Street",
        "phone": "08012345678",
    }


class ModelTests(OrderTestCase):
    def test_totals_and_str(self):
        order = Order.objects.create(user=self.user, **self.checkout_data)
        OrderItem.objects.create(
            order=order, product=self.product, product_name="Python Book",
            unit_price="10.00", quantity=3,
        )
        self.assertEqual(order.total, 30)
        self.assertEqual(str(order), f"Order #{order.pk} by sam")
        self.assertEqual(str(order.items.first()), "3 x Python Book")

    def test_deleting_order_cascades_to_items(self):
        order = Order.objects.create(user=self.user, **self.checkout_data)
        OrderItem.objects.create(
            order=order, product=self.product, product_name="Python Book",
            unit_price="10.00", quantity=1,
        )
        order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_deleting_product_keeps_order_item(self):
        order = Order.objects.create(user=self.user, **self.checkout_data)
        item = OrderItem.objects.create(
            order=order, product=self.product, product_name="Python Book",
            unit_price="10.00", quantity=1,
        )
        self.product.delete()
        item.refresh_from_db()
        self.assertIsNone(item.product)
        self.assertEqual(item.product_name, "Python Book")


class CartTests(OrderTestCase):
    def test_add_to_cart_updates_badge_and_total(self):
        response = self.client.post(
            reverse("orders:cart_add", args=[self.product.pk]),
            {"quantity": 2},
            follow=True,
        )
        self.assertContains(response, "added to your cart")
        self.assertContains(response, "$20.00")

    def test_cart_never_exceeds_stock(self):
        self.add_to_cart(quantity=99)
        response = self.client.get(reverse("orders:cart"))
        self.assertEqual(response.context["items"][0]["quantity"], 5)

    def test_update_and_remove(self):
        self.add_to_cart(quantity=2)
        self.client.post(reverse("orders:cart_update", args=[self.product.pk]), {"quantity": 4})
        self.assertEqual(self.client.get(reverse("orders:cart")).context["items"][0]["quantity"], 4)
        self.client.post(reverse("orders:cart_remove", args=[self.product.pk]))
        self.assertEqual(self.client.get(reverse("orders:cart")).context["items"], [])


class CheckoutTests(OrderTestCase):
    def test_checkout_requires_login(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_empty_cart_redirects(self):
        self.client.login(username="sam", password="pass12345")
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("store:product_list"))

    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username="sam", password="pass12345")
        self.add_to_cart(quantity=2)
        response = self.client.post(
            reverse("orders:checkout"), self.checkout_data, follow=True
        )
        self.assertContains(response, "has been placed")
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total, 20)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        # cart is emptied afterwards
        self.assertEqual(self.client.get(reverse("orders:cart")).context["items"], [])

    def test_invalid_phone_rejected(self):
        self.client.login(username="sam", password="pass12345")
        self.add_to_cart()
        response = self.client.post(
            reverse("orders:checkout"), {**self.checkout_data, "phone": "12"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_stock_changed_since_adding_blocks_checkout(self):
        self.client.login(username="sam", password="pass12345")
        self.add_to_cart(quantity=4)
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        self.client.post(reverse("orders:checkout"), self.checkout_data)
        self.assertEqual(Order.objects.count(), 0)


class OrderHistoryTests(OrderTestCase):
    def make_order(self):
        order = Order.objects.create(user=self.user, **self.checkout_data)
        OrderItem.objects.create(
            order=order, product=self.product, product_name="Python Book",
            unit_price="10.00", quantity=1,
        )
        return order

    def test_order_list_requires_login(self):
        response = self.client.get(reverse("orders:order_list"))
        self.assertEqual(response.status_code, 302)

    def test_owner_can_view_order(self):
        order = self.make_order()
        self.client.login(username="sam", password="pass12345")
        self.assertEqual(
            self.client.get(reverse("orders:order_detail", args=[order.pk])).status_code, 200
        )

    def test_other_user_gets_404(self):
        order = self.make_order()
        self.client.login(username="eve", password="pass12345")
        self.assertEqual(
            self.client.get(reverse("orders:order_detail", args=[order.pk])).status_code, 404
        )
