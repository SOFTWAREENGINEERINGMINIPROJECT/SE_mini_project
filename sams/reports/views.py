from django.db.models import Count, Q
from django.shortcuts import render

from .forms import ReportForm
from .services import build_report

from accounts.decorators import role_required
from attendance.models import AttendanceRecord

THRESHOLD = 75  # BR-4


@role_required("student")
def my_attendance(request):
    """REQ-12: a student sees their own subject-wise attendance %.

    Uses request.user only and never reads a student id from the URL (NFR-8).
    """
    rows = (
        AttendanceRecord.objects.filter(student=request.user)
        .values("subject__code", "subject__name")
        .annotate(
            conducted=Count("id"),
            present=Count("id", filter=Q(status="P")),
            leave=Count("id", filter=Q(status="L")),
        )
        .order_by("subject__code")
    )
    subjects = []
    for r in rows:
        attended = r["present"] + r["leave"]  # BR-5
        pct = round(attended * 100 / r["conducted"], 1) if r["conducted"] else 0
        subjects.append({
            "code": r["subject__code"],
            "name": r["subject__name"],
            "conducted": r["conducted"],
            "attended": attended,
            "percent": pct,
            "below": pct < THRESHOLD,
        })
    return render(request, "reports/my_attendance.html",
                  {"subjects": subjects, "threshold": THRESHOLD})


@role_required("faculty", "admin")
def class_report(request):
    """SEM-15 (REQ-13): attendance report for a class + subject between two dates."""
    form = ReportForm(request.GET or None, user=request.user)
    rows = teaching = start = end = None
    if request.GET and form.is_valid():
        teaching = form.cleaned_data["teaching"]
        start, end = form.cleaned_data["start"], form.cleaned_data["end"]
        rows = build_report(teaching, start, end)
    return render(request, "reports/class_report.html", {
        "form": form, "rows": rows, "teaching": teaching,
        "start": start, "end": end, "threshold": THRESHOLD,
    })