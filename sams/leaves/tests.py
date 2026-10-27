from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LeaveRequest

User = get_user_model()


class ApplyLeaveTests(TestCase):
    """SEM-21 / REQ-17 (part of TC-14)."""

    def setUp(self):
        self.student = User.objects.create_user(username="stud1", password="pw-123456", role="student")
        self.other = User.objects.create_user(username="stud2", password="pw-123456", role="student")
        self.faculty = User.objects.create_user(username="fac1", password="pw-123456", role="faculty")
        self.today = date.today()

    def post(self, start, end, reason="Fever, doctor visit"):
        return self.client.post(reverse("leaves:apply"),
                                {"from_date": start, "to_date": end, "reason": reason})

    def test_student_can_apply_and_request_is_pending(self):
        self.client.force_login(self.student)
        response = self.post(self.today, self.today + timedelta(days=1))
        self.assertRedirects(response, reverse("leaves:my"))
        leave = LeaveRequest.objects.get()
        self.assertEqual(leave.student, self.student)
        self.assertEqual(leave.status, "pending")

    def test_to_date_before_from_date_rejected(self):
        self.client.force_login(self.student)
        response = self.post(self.today, self.today - timedelta(days=1))
        self.assertContains(response, "To date cannot be before from date.")
        self.assertFalse(LeaveRequest.objects.exists())

    def test_overlapping_request_rejected(self):
        self.client.force_login(self.student)
        self.post(self.today, self.today + timedelta(days=2))
        response = self.post(self.today + timedelta(days=1), self.today + timedelta(days=3))
        self.assertContains(response, "already have a leave request")
        self.assertEqual(LeaveRequest.objects.count(), 1)

    def test_rejected_request_does_not_block_new_one(self):
        LeaveRequest.objects.create(student=self.student, from_date=self.today,
                                    to_date=self.today, reason="old one", status="rejected")
        self.client.force_login(self.student)
        self.post(self.today, self.today)
        self.assertEqual(LeaveRequest.objects.filter(status="pending").count(), 1)

    def test_student_sees_only_own_requests(self):  # NFR-8
        LeaveRequest.objects.create(student=self.other, from_date=self.today,
                                    to_date=self.today, reason="someone else")
        LeaveRequest.objects.create(student=self.student, from_date=self.today,
                                    to_date=self.today, reason="mine")
        self.client.force_login(self.student)
        response = self.client.get(reverse("leaves:my"))
        self.assertContains(response, "mine")
        self.assertNotContains(response, "someone else")

    def test_faculty_cannot_apply(self):  # NFR-7
        self.client.force_login(self.faculty)
        self.assertEqual(self.client.get(reverse("leaves:apply")).status_code, 403)

    def test_login_required(self):
        response = self.client.get(reverse("leaves:apply"))
        self.assertEqual(response.status_code, 302)
