"""Session-based shopping cart. Works for anonymous visitors; checkout needs login."""
from store.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    """Stores {product_id: quantity} in the session."""

    def __init__(self, request):
        self.session = request.session
        self.data = dict(self.session.get(CART_SESSION_KEY, {}))

    def _save(self):
        self.session[CART_SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, product, quantity=1):
        key = str(product.pk)
        # Never allow more than the available stock in the cart.
        self.data[key] = min(self.data.get(key, 0) + quantity, product.stock)
        self._save()

    def set_quantity(self, product, quantity):
        if quantity <= 0:
            self.remove(product)
            return
        self.data[str(product.pk)] = min(quantity, product.stock)
        self._save()

    def remove(self, product):
        self.data.pop(str(product.pk), None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def items(self):
        """Cart rows as dicts with product, quantity and line_total."""
        products = Product.objects.in_bulk([int(key) for key in self.data])
        rows = []
        for key, quantity in self.data.items():
            product = products.get(int(key))
            if product is None:  # product was deleted after being added
                continue
            rows.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "line_total": product.price * quantity,
                }
            )
        return rows
