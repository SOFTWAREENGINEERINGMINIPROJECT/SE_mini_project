from django.contrib import messages
from django.contrib.auth import get_user_model
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


# ---- SEM-22 (REQ-18, REQ-19): faculty approve / reject ----

from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from attendance.models import AttendanceLog, AttendanceRecord


def _my_students(faculty):
    """students in any class this faculty teaches"""
    return (
        get_user_model()
        .objects.filter(role="student", classes__teaching__faculty=faculty)
        .distinct()
    )


@role_required("faculty")
def pending_leaves(request):
    leaves = (
        LeaveRequest.objects.filter(status="pending", student__in=_my_students(request.user))
        .select_related("student")
        .order_by("from_date")
    )
    return render(request, "leaves/pending.html", {"leaves": leaves})


@require_POST
@role_required("faculty")
def decide_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk, student__in=_my_students(request.user))
    decision = request.POST.get("decision")
    if decision not in ("approve", "reject"):
        messages.error(request, "Invalid decision.")
        return redirect("leaves:pending")
    if leave.status != "pending":
        messages.warning(request, "This request was already decided.")
        return redirect("leaves:pending")

    with transaction.atomic():
        if decision == "approve":
            leave.status = "approved"
            # REQ-19: absent days inside the leave become Leave (counted as attended, BR-5)
            records = AttendanceRecord.objects.select_for_update().filter(
                student=leave.student,
                date__range=(leave.from_date, leave.to_date),
                status="A",
            )
            for r in records:
                AttendanceLog.objects.create(record=r, changed_by=request.user,
                                             old_status="A", new_status="L")  # NFR-11
            changed = records.update(status="L")
        else:
            leave.status = "rejected"
            changed = 0
        leave.save(update_fields=["status"])

    if leave.student.email:
        send_mail(
            f"Leave request {leave.status}",
            f"Your leave from {leave.from_date:%d %b %Y} to {leave.to_date:%d %b %Y} was {leave.status}.",
            None, [leave.student.email], fail_silently=True,
        )
    extra = f" {changed} absent record(s) marked as Leave." if decision == "approve" else ""
    messages.success(request, f"Leave {leave.status} for {leave.student}.{extra}")
    return redirect("leaves:pending")
