import sys
import types
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academics.models import ClassSection, Subject, Teaching
from attendance.models import AttendanceRecord
from attendance.utils import attendance_percent

User = get_user_model()


class MarkAttendanceTests(TestCase):
    def setUp(self):
        self.faculty = User.objects.create_user("fac", password="x", role="faculty")
        self.other = User.objects.create_user("fac2", password="x", role="faculty")
        self.students = [
            User.objects.create_user(f"s{i}", password="x", role="student", srn=f"PES1UG24CS{i:03d}")
            for i in range(1, 4)
        ]
        self.cls = ClassSection.objects.create(department="CSE", semester=5, section="C")
        self.cls.students.set(self.students)
        self.subject = Subject.objects.create(code="UE24CS341A", name="SE", semester=5)
        self.teaching = Teaching.objects.create(faculty=self.faculty, subject=self.subject, class_section=self.cls)
        self.url = reverse("attendance:mark")
        self.payload = {"teaching": self.teaching.pk, "date": date.today().isoformat(), "hour": 2}

    def test_requires_login_and_faculty_role(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        student = self.students[0]
        self.client.force_login(student)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_lists_all_students(self):
        self.client.force_login(self.faculty)
        resp = self.client.get(self.url, self.payload)
        self.assertEqual(len(resp.context["students"]), 3)

    def test_default_present_and_ticked_absent(self):
        self.client.force_login(self.faculty)
        self.client.post(self.url, {**self.payload, "absent": [self.students[0].pk]})
        recs = {r.student_id: r.status for r in AttendanceRecord.objects.all()}
        self.assertEqual(recs[self.students[0].pk], "A")
        self.assertEqual(recs[self.students[1].pk], "P")
        self.assertEqual(AttendanceRecord.objects.filter(marked_by=self.faculty).count(), 3)

    def test_duplicate_is_rejected(self):
        self.client.force_login(self.faculty)
        self.client.post(self.url, self.payload)
        resp = self.client.post(self.url, self.payload, follow=True)
        self.assertEqual(AttendanceRecord.objects.count(), 3)
        self.assertContains(resp, "Attendance already marked")

    def test_only_assigned_faculty(self):
        self.client.force_login(self.other)
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(AttendanceRecord.objects.count(), 0)
        self.assertFalse(resp.context["form"].is_valid())

    def test_future_date_rejected(self):
        self.client.force_login(self.faculty)
        self.client.post(self.url, {**self.payload, "date": (date.today() + timedelta(days=1)).isoformat()})
        self.assertEqual(AttendanceRecord.objects.count(), 0)


class AttendancePercentTests(TestCase):
    """SEM-13 (REQ-11, BR-5)"""

    def setUp(self):
        self.student = User.objects.create_user("stu", password="x", role="student")
        self.cls = ClassSection.objects.create(department="CSE", semester=5, section="C")
        self.subject = Subject.objects.create(code="UE24CS341A", name="SE", semester=5)
        self.other = Subject.objects.create(code="UE24CS342A", name="DBMS", semester=5)

    def mark(self, statuses, subject=None):
        for i, status in enumerate(statuses):
            AttendanceRecord.objects.create(
                student=self.student, subject=subject or self.subject, class_section=self.cls,
                date=date.today() - timedelta(days=i), hour=1, status=status,
            )

    def test_zero_when_no_classes(self):
        self.assertEqual(attendance_percent(self.student, self.subject), 0)

    def test_present_over_total(self):
        self.mark(["P", "A", "P"])
        self.assertEqual(attendance_percent(self.student, self.subject), 66.67)

    def test_leave_counts_as_attended(self):
        self.mark(["P", "L", "A", "A"])
        self.assertEqual(attendance_percent(self.student, self.subject), 50.0)

    def test_scoped_to_subject_and_student(self):
        self.mark(["A", "A"])
        self.mark(["P"], subject=self.other)
        User.objects.create_user("stu2", password="x", role="student")
        self.assertEqual(attendance_percent(self.student, self.subject), 0.0)
        self.assertEqual(attendance_percent(self.student, self.other), 100.0)


class ShortageHookTests(MarkAttendanceTests):
    def test_hook_runs_per_student_after_save(self):
        self.client.force_login(self.faculty)
        calls = []
        fake = types.SimpleNamespace(check_shortage=lambda s, sub: calls.append((s.pk, sub.pk)))
        with mock.patch.dict(sys.modules, {"leaves.utils": fake}):
            self.client.post(self.url, self.payload)
        self.assertEqual(sorted(calls), sorted((s.pk, self.subject.pk) for s in self.students))

    def test_mail_failure_does_not_break_saving(self):
        self.client.force_login(self.faculty)

        def boom(s, sub):
            raise RuntimeError("smtp down")

        with mock.patch.dict(sys.modules, {"leaves.utils": types.SimpleNamespace(check_shortage=boom)}):
            self.client.post(self.url, self.payload)
        self.assertEqual(AttendanceRecord.objects.count(), 3)

    def test_missing_check_shortage_is_noop(self):
        self.client.force_login(self.faculty)
        self.client.post(self.url, self.payload)  # leaves.utils absent until SEM-20
        self.assertEqual(AttendanceRecord.objects.count(), 3)
