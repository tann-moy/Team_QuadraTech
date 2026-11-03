from functools import wraps
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(role):
    """Allow only users whose profile.role matches (e.g. 'tenant' or 'owner')."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if profile is None or profile.role != role:
                raise PermissionDenied
            if not profile.is_verified:        # admin un-verified a logged-in user
                logout(request)
                messages.error(request, "Your account is not verified.")
                return redirect("accounts:login")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
