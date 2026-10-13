from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    """Land every role on its own dashboard template after login (REQ-2)."""
    return render(request, f"accounts/dashboard_{request.user.role}.html")
