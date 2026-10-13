from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Restrict a view to the given User.role values. Requires login first (NFR-7).

    Not logged in -> redirected to LOGIN_URL (django's usual behaviour).
    Logged in, wrong role -> 403, not a redirect loop back to login.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied("Your role does not have access to this page.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
