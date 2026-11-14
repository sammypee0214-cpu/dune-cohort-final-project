from .cart import CART_SESSION_KEY


def cart_count(request):
    """Expose the number of items in the cart to every template (navbar badge)."""
    cart = request.session.get(CART_SESSION_KEY, {})
    return {"cart_count": sum(cart.values())}
