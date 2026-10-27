from django.db.models import Count, Q

from attendance.models import AttendanceRecord

THRESHOLD = 75  # BR-4


def build_report(teaching, start, end):
    """Attendance of every student in teaching's class for its subject between two dates.

    Shared by the on-screen report (SEM-15) and the exports (SEM-16).
    Attended = Present + Leave (BR-5).
    """
    students = teaching.class_section.students.filter(role="student").order_by("srn", "username")
    counts = {
        r["student"]: r
        for r in AttendanceRecord.objects.filter(
            subject=teaching.subject,
            class_section=teaching.class_section,
            date__range=(start, end),
        )
        .values("student")
        .annotate(
            conducted=Count("id"),
            present=Count("id", filter=Q(status="P")),
            leave=Count("id", filter=Q(status="L")),
        )
    }
    rows = []
    for s in students:
        c = counts.get(s.pk, {"conducted": 0, "present": 0, "leave": 0})
        attended = c["present"] + c["leave"]
        pct = round(attended * 100 / c["conducted"], 1) if c["conducted"] else 0
        rows.append({
            "srn": s.srn,
            "name": s.get_full_name() or s.username,
            "conducted": c["conducted"],
            "attended": attended,
            "absent": c["conducted"] - attended,
            "percent": pct,
            "below": c["conducted"] > 0 and pct < THRESHOLD,
        })
    return rows