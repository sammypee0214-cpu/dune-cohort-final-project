# Dune Shop - E-commerce Store

Dune Cohort · Backend Development with Python & Django · Module 16 Final Project

## Live site

**https://YOUR-APP.onrender.com**  <!-- replace with your real Render URL -->

- Admin: `/admin/`
- REST API: `/api/products/`

## What it does

An online store. Visitors browse, search and filter products, and fill a cart.
Registered customers check out and view their order history. Staff users manage
the catalogue (add, edit, delete products) and update order status in the admin.

## Apps and models

| App | Responsibility |
| --- | --- |
| `store` | Categories, products, product CRUD, REST API |
| `orders` | Session cart, checkout, orders and order items |
| `accounts` | Registration, login, logout |

| Model | App | Relationships |
| --- | --- | --- |
| `Category` | store | Has many `Product` |
| `Product` | store | FK to `Category` (`CASCADE`); has an `ImageField` |
| `Order` | orders | FK to `User` (`CASCADE`) |
| `OrderItem` | orders | FK to `Order` (`CASCADE`), FK to `Product` (`SET_NULL`) |

Order items store a snapshot of the product name and price, so order history
stays correct even if a product is later edited or deleted.

## Pages

| URL | Page | Access |
| --- | --- | --- |
| `/` | Product list (search + category filter) | Public |
| `/products/<pk>/` | Product detail | Public |
| `/category/<slug>/` | Products in a category | Public |
| `/cart/` | Shopping cart | Public |
| `/checkout/` | Checkout | Login required |
| `/orders/`, `/orders/<pk>/` | Order history and detail | Login required |
| `/products/add/` | Create product | Staff only |
| `/products/<pk>/edit/` | Edit product | Staff only |
| `/products/<pk>/delete/` | Delete product | Staff only |
| `/accounts/register/`, `/accounts/login/` | Auth | Public |

## REST API

| Method | Endpoint | Auth | Success | Errors |
| --- | --- | --- | --- | --- |
| GET | `/api/products/` | No | 200 | |
| POST | `/api/products/` | Staff | 201 | 400, 401, 403 |
| GET | `/api/products/<id>/` | No | 200 | 404 |
| DELETE | `/api/products/<id>/` | Staff | 204 | 401, 403, 404 |

`PUT`/`PATCH` on `/api/products/<id>/` are also available (staff only). Auth is
HTTP Basic (username and password of a staff user) or a logged-in staff session.

The Postman collection is in [`postman/dune-shop-api.postman_collection.json`](postman/dune-shop-api.postman_collection.json).
Import it, set the `base_url`, `username`, `password` and `category_id`
collection variables, then run the collection in order.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DEBUG=True                  # Windows PowerShell: $env:DEBUG="True"
python manage.py migrate
python manage.py seed_demo         # starter categories and products
python manage.py createsuperuser   # staff account for managing products
python manage.py runserver
```

Run the tests with `DEBUG=True python manage.py test`.

## Deploy on Render

1. Create a **PostgreSQL** database on Render and copy its *Internal Database URL*.
2. Create a **Web Service** from this GitHub repo with:
   - Build command: `bash build.sh`
   - Start command: `gunicorn config.wsgi:application`
3. Add environment variables:

   | Key | Value |
   | --- | --- |
   | `SECRET_KEY` | a long random string |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | the Internal Database URL from step 1 |
   | `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` | creates the staff admin on first deploy |

4. Deploy, then visit your `https://...onrender.com` URL.

`build.sh` installs dependencies, runs `collectstatic` (served by WhiteNoise),
applies migrations and seeds the demo catalogue.

### Known limitation

Render's free web services have an ephemeral disk, so product images uploaded
through the site are lost on redeploy. Production use would need object storage
such as S3 or Cloudinary.
