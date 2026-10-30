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


class ApproveLeaveTests(TestCase):
    """SEM-22 / REQ-18, REQ-19 (TC-14)."""

    def setUp(self):
        from academics.models import ClassSection, Subject, Teaching
        from attendance.models import AttendanceRecord

        self.Record = AttendanceRecord
        self.fac = User.objects.create_user(username="fac1", password="pw-123456", role="faculty")
        self.other_fac = User.objects.create_user(username="fac2", password="pw-123456", role="faculty")
        self.stud = User.objects.create_user(username="stud1", password="pw-123456", role="student",
                                             email="s@example.com")
        self.cls = ClassSection.objects.create(department="CSE", semester=5, section="C")
        self.cls.students.add(self.stud)
        self.sub = Subject.objects.create(code="UE24CS341A", name="SE", semester=5)
        Teaching.objects.create(faculty=self.fac, subject=self.sub, class_section=self.cls)
        self.d1 = date.today() - timedelta(days=2)
        self.d2 = date.today() - timedelta(days=1)
        for d, st in [(self.d1, "A"), (self.d2, "P"), (date.today(), "A")]:
            AttendanceRecord.objects.create(student=self.stud, subject=self.sub, class_section=self.cls,
                                            date=d, hour=1, status=st, marked_by=self.fac)
        self.leave = LeaveRequest.objects.create(student=self.stud, from_date=self.d1, to_date=self.d2,
                                                 reason="fever")

    def decide(self, decision, user=None):
        self.client.force_login(user or self.fac)
        return self.client.post(reverse("leaves:decide", args=[self.leave.pk]), {"decision": decision})

    def test_faculty_sees_pending_request(self):
        self.client.force_login(self.fac)
        self.assertContains(self.client.get(reverse("leaves:pending")), "fever")

    def test_approve_marks_absent_days_in_range_as_leave(self):
        from attendance.models import AttendanceLog
        self.decide("approve")
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, "approved")
        self.assertEqual(self.Record.objects.get(date=self.d1).status, "L")
        self.assertEqual(self.Record.objects.get(date=self.d2).status, "P")         # present stays present
        self.assertEqual(self.Record.objects.get(date=date.today()).status, "A")   # outside range
        self.assertEqual(AttendanceLog.objects.count(), 1)                          # NFR-11

    def test_approved_leave_counts_in_percentage(self):  # REQ-19 / BR-5
        self.decide("approve")
        self.client.force_login(self.stud)
        self.assertContains(self.client.get(reverse("reports:my")), "66.7%")

    def test_reject_leaves_records_alone(self):
        self.decide("reject")
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, "rejected")
        self.assertEqual(self.Record.objects.get(date=self.d1).status, "A")

    def test_cannot_decide_twice(self):
        self.decide("reject")
        self.decide("approve")
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, "rejected")

    def test_other_faculty_cannot_decide(self):
        self.assertEqual(self.decide("approve", user=self.other_fac).status_code, 404)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, "pending")

    def test_student_cannot_decide(self):  # NFR-7
        self.assertEqual(self.decide("approve", user=self.stud).status_code, 403)

    def test_get_not_allowed(self):
        self.client.force_login(self.fac)
        self.assertEqual(self.client.get(reverse("leaves:decide", args=[self.leave.pk])).status_code, 405)


class ShortageEmailTests(TestCase):
    """SEM-20 / REQ-16 (TC-13)."""

    def setUp(self):
        from academics.models import ClassSection, Subject, Teaching

        self.fac = User.objects.create_user(username="fac9", password="pw-123456", role="faculty")
        self.stud = User.objects.create_user(username="stud9", password="pw-123456", role="student",
                                             email="stud9@example.com", first_name="Ravi")
        self.cls = ClassSection.objects.create(department="CSE", semester=5, section="A")
        self.cls.students.add(self.stud)
        self.sub = Subject.objects.create(code="UE24CS342A", name="Compilers", semester=5)
        Teaching.objects.create(faculty=self.fac, subject=self.sub, class_section=self.cls)

    def add(self, status, hour):
        from attendance.models import AttendanceRecord
        AttendanceRecord.objects.create(student=self.stud, subject=self.sub, class_section=self.cls,
                                        date=date.today(), hour=hour, status=status, marked_by=self.fac)

    def test_mail_sent_when_below_75(self):
        from django.core import mail
        from .utils import check_shortage
        self.add("P", 1); self.add("A", 2)          # 50%
        self.assertTrue(check_shortage(self.stud, self.sub))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["stud9@example.com"])
        self.assertIn("50.0%", mail.outbox[0].body)

    def test_no_mail_at_exactly_75(self):          # boundary, BR-4
        from django.core import mail
        from .utils import check_shortage
        for h, st in enumerate("PPPA", start=1):
            self.add(st, h)
        self.assertFalse(check_shortage(self.stud, self.sub))
        self.assertEqual(len(mail.outbox), 0)

    def test_not_resent_within_a_week(self):
        from django.core import mail
        from .utils import check_shortage
        self.add("A", 1)
        check_shortage(self.stud, self.sub)
        self.add("A", 2)
        self.assertFalse(check_shortage(self.stud, self.sub))
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_address_no_mail(self):
        from django.core import mail
        from .utils import check_shortage
        self.stud.email = ""
        self.stud.save()
        self.add("A", 1)
        self.assertFalse(check_shortage(self.stud, self.sub))
        self.assertEqual(len(mail.outbox), 0)

    def test_marking_attendance_triggers_mail(self):  # end to end through SEM-11 + SEM-13 hook
        from django.core import mail
        from academics.models import Teaching
        t = Teaching.objects.get()
        self.client.force_login(self.fac)
        self.client.post(reverse("attendance:mark"), {
            "teaching": t.pk, "date": date.today(), "hour": 1, "absent": [str(self.stud.pk)],
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("UE24CS342A", mail.outbox[0].subject)


class ShortageBoundaryTests(TestCase):
    setUp = ShortageEmailTests.setUp
    add = ShortageEmailTests.add

    def test_mail_once_it_drops_below_75(self):
        """3/4 = 75% is not a shortage, one more absent (3/5 = 60%) is (BR-4)."""
        from django.core import mail
        from .utils import check_shortage
        for h, st in enumerate("PPPA", start=1):
            self.add(st, h)
        self.add("A", 5)  # 3/5 = 60%
        self.assertTrue(check_shortage(self.stud, self.sub))
        self.assertEqual(len(mail.outbox), 1)
