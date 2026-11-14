from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Category, Product


class StoreTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            category=self.category, name="Headphones", price="59.99", stock=5
        )
        self.customer = User.objects.create_user("sam", password="pass12345")
        self.staff = User.objects.create_user(
            "boss", password="pass12345", is_staff=True
        )

    def product_form_data(self, **overrides):
        data = {
            "category": self.category.pk,
            "name": "Speaker",
            "description": "",
            "price": "25.00",
            "stock": 10,
        }
        data.update(overrides)
        return data


class ModelTests(StoreTestCase):
    def test_str_and_slug(self):
        self.assertEqual(str(self.category), "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertEqual(str(self.product), "Headphones")

    def test_deleting_category_cascades_to_products(self):
        self.category.delete()
        self.assertEqual(Product.objects.count(), 0)


class PageTests(StoreTestCase):
    def test_public_pages_load(self):
        for name, args in [
            ("store:product_list", []),
            ("store:product_detail", [self.product.pk]),
            ("store:category_detail", [self.category.slug]),
        ]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_unknown_product_is_404(self):
        self.assertEqual(
            self.client.get(reverse("store:product_detail", args=[999])).status_code, 404
        )

    def test_search_filters_products(self):
        response = self.client.get(reverse("store:product_list"), {"q": "zzz"})
        self.assertContains(response, "No products match")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("store:product_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_customer_cannot_create_product(self):
        self.client.login(username="sam", password="pass12345")
        self.client.post(reverse("store:product_create"), self.product_form_data())
        self.assertEqual(Product.objects.count(), 1)

    def test_staff_full_crud(self):
        self.client.login(username="boss", password="pass12345")

        response = self.client.post(
            reverse("store:product_create"), self.product_form_data(), follow=True
        )
        self.assertContains(response, "was added to the store")
        created = Product.objects.get(name="Speaker")

        response = self.client.post(
            reverse("store:product_update", args=[created.pk]),
            self.product_form_data(name="Speaker Pro"),
            follow=True,
        )
        self.assertContains(response, "was updated")

        response = self.client.post(
            reverse("store:product_delete", args=[created.pk]), follow=True
        )
        self.assertContains(response, "was deleted")
        self.assertFalse(Product.objects.filter(pk=created.pk).exists())

    def test_invalid_product_rejected(self):
        self.client.login(username="boss", password="pass12345")
        response = self.client.post(
            reverse("store:product_create"), self.product_form_data(name="ab")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)


class RegistrationTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "a-Strong-pass-123",
                "password2": "a-Strong-pass-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())


class APITests(StoreTestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.payload = {
            "category": self.category.pk,
            "name": "Charger",
            "price": "15.00",
            "stock": 3,
        }

    def test_list_is_public(self):
        response = self.api.get("/api/products/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_detail_and_404(self):
        self.assertEqual(self.api.get(f"/api/products/{self.product.pk}/").status_code, 200)
        self.assertEqual(self.api.get("/api/products/9999/").status_code, 404)

    def test_anonymous_write_is_401(self):
        response = self.api.post("/api/products/", self.payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_non_staff_write_is_403(self):
        self.api.force_authenticate(self.customer)
        response = self.api.post("/api/products/", self.payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_staff_create_returns_201(self):
        self.api.force_authenticate(self.staff)
        response = self.api.post("/api/products/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category_name"], "Electronics")

    def test_invalid_create_returns_400(self):
        self.api.force_authenticate(self.staff)
        response = self.api.post("/api/products/", {"name": "x"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_staff_delete_returns_204(self):
        self.api.force_authenticate(self.staff)
        response = self.api.delete(f"/api/products/{self.product.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
