from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from accounts.decorators import role_required

from .forms import SelectClassForm
from leaves.models import LeaveRequest

from .models import AttendanceRecord


@role_required("faculty")
def mark_attendance(request):
    """SEM-11 (REQ-8, REQ-9): pick subject+class+date+hour, everyone Present by default,
    tick absentees, save. GET without params shows the picker; GET with params shows the
    student list; POST saves."""
    data = request.POST if request.method == "POST" else (request.GET or None)
    form = SelectClassForm(data, faculty=request.user)
    students = None
    teaching = None

    if data is not None and form.is_valid():
        teaching = form.cleaned_data["teaching"]
        day, hour = form.cleaned_data["date"], form.cleaned_data["hour"]
        students = teaching.class_section.students.filter(role="student").order_by("srn", "username")

        already = AttendanceRecord.objects.filter(
            subject=teaching.subject, class_section=teaching.class_section, date=day, hour=hour
        ).exists()
        if already:
            messages.warning(request, "Attendance already marked for this subject, date and hour.")
            students = None
        elif request.method == "POST":
            absent_ids = set(request.POST.getlist("absent"))
            on_leave = set(
                LeaveRequest.objects.filter(
                    status="approved", from_date__lte=day, to_date__gte=day, student__in=students
                ).values_list("student_id", flat=True)
            )
            try:
                with transaction.atomic():
                    AttendanceRecord.objects.bulk_create(
                        AttendanceRecord(
                            student=s,
                            subject=teaching.subject,
                            class_section=teaching.class_section,
                            date=day,
                            hour=hour,
                            status=("L" if s.pk in on_leave else "A") if str(s.pk) in absent_ids else "P",
                            marked_by=request.user,
                        )
                        for s in students
                    )
            except IntegrityError:
                # lost a race with another save of the same slot (REQ-9)
                messages.warning(request, "Attendance already marked for this subject, date and hour.")
                students = None
            else:
                messages.success(
                    request,
                    f"Attendance saved for {teaching.subject.code} ({teaching.class_section}), "
                    f"{day:%d %b %Y}, hour {hour}: {len(absent_ids & {str(s.pk) for s in students})} absent.",
                )
                return redirect("attendance:mark")

    return render(request, "attendance/mark.html", {"form": form, "students": students, "teaching": teaching})
