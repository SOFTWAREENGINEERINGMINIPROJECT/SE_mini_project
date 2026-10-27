from django.db.models import Count, Q

from .models import AttendanceRecord


def attendance_percent(student, subject):
    """SEM-13 (REQ-11, BR-5): (Present + Leave) / total * 100, 2 decimals, 0 if no classes yet.

    The one place the formula lives: reports (SEM-17) and leaves (SEM-20) import this.
    """
    counts = AttendanceRecord.objects.filter(student=student, subject=subject).aggregate(
        total=Count("id"),
        attended=Count("id", filter=Q(status__in=("P", "L"))),
    )
    if not counts["total"]:
        return 0
    return round(counts["attended"] * 100 / counts["total"], 2)


def run_shortage_check(students, subject):
    """Shortage hook: call check_shortage(student, subject) for each student after a class is saved.

    check_shortage lives in leaves/utils.py (SEM-20). Until that merges this is a no-op,
    so SEM-13 can ship first; a mail problem never breaks saving attendance.
    """
    try:
        from leaves.utils import check_shortage
    except ImportError:
        return
    for s in students:
        try:
            check_shortage(s, subject)
        except Exception:  # noqa: BLE001 - attendance is already saved, don't fail the request
            pass
