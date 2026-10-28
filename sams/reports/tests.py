from datetime import date

from django.test import TestCase
from django.urls import reverse

from academics.models import ClassSection, Subject, Teaching
from accounts.models import User
from attendance.models import AttendanceRecord


class ClassReportTests(TestCase):
    def setUp(self):
        self.fac = User.objects.create_user("fac", password="x", role="faculty")
        self.other_fac = User.objects.create_user("fac2", password="x", role="faculty")
        self.stu = User.objects.create_user("stu", password="x", role="student", srn="S1")
        cls = ClassSection.objects.create(department="CSE", semester=3, section="C")
        cls.students.add(self.stu)
        sub = Subject.objects.create(code="SE", name="Software Eng", semester=3)
        self.teaching = Teaching.objects.create(faculty=self.fac, subject=sub, class_section=cls)
        for i, status in enumerate("PPPA"):  # 3 of 4 = 75%
            AttendanceRecord.objects.create(
                student=self.stu, subject=sub, class_section=cls,
                date=date(2026, 10, 1 + i), hour=1, status=status, marked_by=self.fac,
            )
        self.url = reverse("reports:class")

    def get(self, start="2026-10-01", end="2026-10-31"):
        return self.client.get(self.url, {"teaching": self.teaching.pk, "start": start, "end": end})

    def test_faculty_sees_percentage(self):
        self.client.login(username="fac", password="x")
        row = self.get().context["rows"][0]
        self.assertEqual((row["conducted"], row["attended"], row["absent"]), (4, 3, 1))
        self.assertEqual(row["percent"], 75.0)
        self.assertFalse(row["below"])  # exactly 75% is not below the threshold (BR-4)

    def test_date_range_limits_records(self):
        self.client.login(username="fac", password="x")
        row = self.get(end="2026-10-02").context["rows"][0]
        self.assertEqual((row["conducted"], row["percent"]), (2, 100.0))

    def test_start_after_end_is_rejected(self):
        self.client.login(username="fac", password="x")
        self.assertIsNone(self.get(start="2026-10-31", end="2026-10-01").context["rows"])

    def test_faculty_cannot_report_on_another_facultys_class(self):
        self.client.login(username="fac2", password="x")
        self.assertIsNone(self.get().context["rows"])

    def test_student_forbidden(self):
        self.client.login(username="stu", password="x")
        self.assertEqual(self.get().status_code, 403)

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.get().status_code, 302)

class ShortageListTests(TestCase):
    def setUp(self):
        self.fac = User.objects.create_user("fac", password="x", role="faculty")
        self.other_fac = User.objects.create_user("fac2", password="x", role="faculty")
        self.admin = User.objects.create_user("adm", password="x", role="admin")
        self.low = User.objects.create_user("low", password="x", role="student", srn="S1")
        self.edge = User.objects.create_user("edge", password="x", role="student", srn="S2")
        self.fresh = User.objects.create_user("fresh", password="x", role="student", srn="S3")
        cls = ClassSection.objects.create(department="CSE", semester=3, section="C")
        cls.students.add(self.low, self.edge, self.fresh)
        self.sub = Subject.objects.create(code="SE", name="Software Eng", semester=3)
        Teaching.objects.create(faculty=self.fac, subject=self.sub, class_section=cls)
        self.cls = cls
        # low: 1 of 4 = 25%; edge: 3 of 4 = exactly 75%; fresh: no classes yet
        for student, pattern in ((self.low, "PAAA"), (self.edge, "PPPA")):
            for i, status in enumerate(pattern):
                AttendanceRecord.objects.create(
                    student=student, subject=self.sub, class_section=cls,
                    date=date(2026, 10, 1 + i), hour=1, status=status, marked_by=self.fac,
                )
        self.url = reverse("reports:shortage")

    def names(self, response):
        return [r["name"] for r in response.context["rows"]]

    def test_lists_only_students_below_75(self):
        self.client.login(username="fac", password="x")
        response = self.client.get(self.url)
        self.assertEqual(self.names(response), ["low"])  # 75% exactly and no-classes are not listed
        self.assertEqual(response.context["rows"][0]["percent"], 25.0)

    def test_admin_sees_all_classes(self):
        self.client.login(username="adm", password="x")
        self.assertEqual(self.names(self.client.get(self.url)), ["low"])

    def test_other_faculty_sees_nothing(self):
        self.client.login(username="fac2", password="x")
        self.assertEqual(self.names(self.client.get(self.url)), [])

    def test_student_forbidden(self):
        self.client.login(username="low", password="x")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)