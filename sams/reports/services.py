from django.db.models import Count, Q

from attendance.models import AttendanceRecord
from attendance.utils import attendance_percent
from leaves.models import ShortageAlert

THRESHOLD = 75  # BR-4


def is_below(attended, conducted):
    """BR-4: below 75%, compared exactly (no rounding).

    `attended` must already include approved leave (BR-5).
    """
    return conducted > 0 and attended * 100 < THRESHOLD * conducted


def faculty_name(teaching):
    f = teaching.faculty
    return (f.get_full_name() or f.username) if f else ""


def build_report(teaching, start, end):
    """Attendance of every student in teaching's class for its subject between two dates.

    Shared by the on-screen report (SEM-15) and the exports (SEM-16).
    Columns follow SRS Appendix B: conducted, attended (present), leave days, attendance %.
    Attendance % = (present + approved leave) / conducted x 100 (BR-5).
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
        covered = c["present"] + c["leave"]
        rows.append({
            "srn": s.srn,
            "name": s.get_full_name() or s.username,
            "conducted": c["conducted"],
            "attended": c["present"],
            "leave": c["leave"],
            "absent": c["conducted"] - covered,
            "percent": round(covered * 100 / c["conducted"], 1) if c["conducted"] else 0,
            "below": is_below(covered, c["conducted"]),
        })
    return rows


def build_shortage(teachings):
    """SEM-17 (REQ-15, BR-4): students below THRESHOLD % in each given teaching (subject + class).

    Columns follow the SRS Appendix B shortage report. The displayed % comes from
    attendance_percent() (SEM-13); the below-75 decision is exact (see is_below).
    Students with no classes conducted yet are not listed.
    """
    rows = []
    for t in teachings:
        counts = {
            r["student"]: r
            for r in AttendanceRecord.objects.filter(subject=t.subject, class_section=t.class_section)
            .values("student")
            .annotate(
                total=Count("id"),
                present=Count("id", filter=Q(status="P")),
                leave=Count("id", filter=Q(status="L")),
            )
        }
        mailed = set(
            ShortageAlert.objects.filter(subject=t.subject).values_list("student_id", flat=True)
        )
        faculty = faculty_name(t)
        students = t.class_section.students.filter(role="student").order_by("srn", "username")
        for s in students:
            c = counts.get(s.pk)
            if not c or not is_below(c["present"] + c["leave"], c["total"]):
                continue
            rows.append({
                "srn": s.srn,
                "name": s.get_full_name() or s.username,
                "subject": t.subject,
                "class_section": t.class_section,
                "conducted": c["total"],
                "attended": c["present"],
                "leave": c["leave"],
                "percent": attendance_percent(s, t.subject),
                "email_sent": s.pk in mailed,
                "faculty": faculty,
            })
    rows.sort(key=lambda r: (r["percent"], r["srn"] or ""))
    return rows