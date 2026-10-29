from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import role_required
from attendance.models import AttendanceRecord

from .exports import build_pdf, build_xlsx, report_filename
from .forms import ReportForm, ShortageFilterForm
from .services import THRESHOLD, build_report, build_shortage, faculty_name, is_below


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
        subjects.append({
            "code": r["subject__code"],
            "name": r["subject__name"],
            "conducted": r["conducted"],
            "attended": attended,
            "percent": round(attended * 100 / r["conducted"], 1) if r["conducted"] else 0,
            "below": is_below(attended, r["conducted"]),  # exact, BR-4
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
        "faculty": faculty_name(teaching) if teaching else "",
        "generated_on": timezone.localtime(),
    })


EXPORTS = {
    "pdf": (build_pdf, "application/pdf"),
    "xlsx": (build_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
}


@role_required("faculty", "admin")
def export_class_report(request, fmt):
    """SEM-16 (REQ-14): download the SEM-15 report as PDF or Excel.

    Same inputs and same access rules as the on-screen report.
    """
    if fmt not in EXPORTS:
        raise Http404("Unknown export format")
    form = ReportForm(request.GET, user=request.user)
    if not form.is_valid():
        return HttpResponseBadRequest("Choose a class and a valid date range first.")
    teaching = form.cleaned_data["teaching"]
    start, end = form.cleaned_data["start"], form.cleaned_data["end"]
    rows = build_report(teaching, start, end)
    build, content_type = EXPORTS[fmt]
    response = HttpResponse(
        build(teaching, start, end, rows, timezone.localtime()), content_type=content_type
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{report_filename(teaching, start, end, fmt)}"'
    )
    return response


@role_required("faculty", "admin")
def shortage_list(request):
    """SEM-17 (REQ-15): students below 75% attendance.

    Faculty see their own classes; admin sees every class.
    """
    form = ShortageFilterForm(request.GET or None, user=request.user)
    teachings = form.fields["teaching"].queryset
    if request.GET and form.is_valid() and form.cleaned_data["teaching"]:
        teachings = teachings.filter(pk=form.cleaned_data["teaching"].pk)
    rows = build_shortage(teachings)
    return render(request, "reports/shortage_list.html", {
        "form": form, "rows": rows, "threshold": THRESHOLD,
        "generated_on": timezone.localtime(),
    })