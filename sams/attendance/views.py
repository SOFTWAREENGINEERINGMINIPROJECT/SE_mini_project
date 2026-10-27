from datetime import timedelta

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required

from .forms import SelectClassForm
from leaves.models import LeaveRequest

from .models import AttendanceLog, AttendanceRecord
from .utils import run_shortage_check


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
                run_shortage_check(students, teaching.subject)  # SEM-13 hook
                messages.success(
                    request,
                    f"Attendance saved for {teaching.subject.code} ({teaching.class_section}), "
                    f"{day:%d %b %Y}, hour {hour}: {len(absent_ids & {str(s.pk) for s in students})} absent.",
                )
                return redirect("attendance:mark")

    return render(request, "attendance/mark.html", {"form": form, "students": students, "teaching": teaching})


EDIT_WINDOW = timedelta(days=3)


@role_required("faculty", "admin")
def edit_attendance(request):
    """SEM-12 (REQ-10, BR-3, NFR-11): correct already-marked attendance.

    Faculty (only for their own classes) can edit within 3 days of marking it; after that only
    Admin can. Every changed status writes an AttendanceLog row. Nothing is ever deleted (NFR-5)."""
    is_admin = request.user.role == "admin"
    data = request.POST if request.method == "POST" else (request.GET or None)
    form = SelectClassForm(data, faculty=request.user, all_classes=is_admin)
    records = None
    teaching = None
    locked = False

    if data is not None and form.is_valid():
        teaching = form.cleaned_data["teaching"]
        day, hour = form.cleaned_data["date"], form.cleaned_data["hour"]
        records = list(
            AttendanceRecord.objects.filter(
                subject=teaching.subject, class_section=teaching.class_section, date=day, hour=hour
            )
            .select_related("student")
            .order_by("student__srn", "student__username")
        )
        if not records:
            messages.warning(request, "Attendance has not been marked for this subject, date and hour yet.")
            records = None
        else:
            first_marked = min(r.marked_at for r in records)
            locked = not is_admin and timezone.now() - first_marked > EDIT_WINDOW
            if locked:
                messages.warning(
                    request, "This attendance was marked more than 3 days ago. Only an Admin can change it now."
                )
            elif request.method == "POST":
                valid = {code for code, _ in AttendanceRecord.STATUS}
                changed = []
                with transaction.atomic():
                    for rec in AttendanceRecord.objects.select_for_update().filter(pk__in=[r.pk for r in records]):
                        new = request.POST.get(f"status_{rec.student_id}")
                        if new in valid and new != rec.status:
                            AttendanceLog.objects.create(
                                record=rec, changed_by=request.user, old_status=rec.status, new_status=new
                            )
                            rec.status = new
                            rec.save(update_fields=["status"])
                            changed.append(rec.student)
                if changed:
                    run_shortage_check(changed, teaching.subject)  # percentages changed (REQ-11)
                    messages.success(request, f"Attendance updated: {len(changed)} change(s) saved and logged.")
                else:
                    messages.info(request, "No changes to save.")
                return redirect("attendance:edit")

    return render(
        request,
        "attendance/edit.html",
        {"form": form, "records": None if locked else records, "teaching": teaching, "statuses": AttendanceRecord.STATUS},
    )
