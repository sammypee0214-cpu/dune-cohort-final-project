from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(view_func):
    """Require a logged-in staff user. Others are redirected with a message."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Only staff members can manage products.")
            return redirect("store:product_list")
        return view_func(request, *args, **kwargs)

    return wrapper
