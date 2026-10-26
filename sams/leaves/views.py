from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.decorators import role_required

from .forms import LeaveRequestForm
from .models import LeaveRequest


@role_required("student")
def apply_leave(request):
    """SEM-21 (REQ-17): student applies for leave. New requests start as Pending."""
    form = LeaveRequestForm(request.POST or None, student=request.user)
    if request.method == "POST" and form.is_valid():
        leave = form.save(commit=False)
        leave.student = request.user  # never taken from the form (NFR-8)
        leave.status = "pending"
        leave.save()
        messages.success(request, "Leave request submitted.")
        return redirect("leaves:my")
    return render(request, "leaves/apply.html", {"form": form})


@role_required("student")
def my_leaves(request):
    """Student sees only their own leave requests and the status of each."""
    leaves = LeaveRequest.objects.filter(student=request.user).order_by("-created_at")
    return render(request, "leaves/my_leaves.html", {"leaves": leaves})
