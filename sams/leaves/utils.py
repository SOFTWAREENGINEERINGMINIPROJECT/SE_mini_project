from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from django.db.models import Count, Q

from attendance.models import AttendanceRecord
from attendance.utils import attendance_percent

from .models import ShortageAlert

THRESHOLD = 75          # BR-4
RESEND_AFTER_DAYS = 7   # don't mail the same student for the same subject every class


def check_shortage(student, subject):
    """SEM-20 (REQ-16): email the student if their attendance in `subject` is below 75%.

    Called from attendance.utils.run_shortage_check() after every saved class.
    Returns True if a mail was sent.
    """
    if not student.email:
        return False
    counts = AttendanceRecord.objects.filter(student=student, subject=subject).aggregate(
        total=Count("id"), attended=Count("id", filter=Q(status__in=("P", "L")))
    )
    # exact comparison (BR-4), same rule as the shortage list - no rounding at the 75% boundary
    if not counts["total"] or counts["attended"] * 100 >= THRESHOLD * counts["total"]:
        return False
    pct = attendance_percent(student, subject)

    recent = ShortageAlert.objects.filter(
        student=student, subject=subject,
        sent_at__gte=timezone.now() - timedelta(days=RESEND_AFTER_DAYS),
    ).exists()
    if recent:
        return False

    name = student.get_full_name() or student.username
    send_mail(
        subject=f"Attendance shortage: {subject.code}",
        message=(
            f"Hi {name},\n\n"
            f"Your attendance in {subject.code} - {subject.name} is {pct}%, "
            f"which is below the required {THRESHOLD}%.\n"
            f"Please attend the upcoming classes to avoid being detained from ESA.\n\n"
            f"- SAMS"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student.email],
        fail_silently=False,
    )
    ShortageAlert.objects.create(student=student, subject=subject, percent=pct)
    return True
