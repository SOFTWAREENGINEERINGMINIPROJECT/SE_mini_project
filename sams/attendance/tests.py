from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academics.models import ClassSection, Subject, Teaching
from attendance.models import AttendanceRecord

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
