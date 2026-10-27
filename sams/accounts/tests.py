from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .decorators import role_required

User = get_user_model()


class LoginTests(TestCase):
    """REQ-1. TC-01: valid login opens the dashboard. TC-02: wrong password shows the SRS wording."""

    def setUp(self):
        self.user = User.objects.create_user(username="stud1", password="correct-pw", role="student")

    def test_valid_login_redirects_to_dashboard(self):  # TC-01
        response = self.client.post(reverse("accounts:login"), {"username": "stud1", "password": "correct-pw"})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_wrong_password_shows_invalid_credentials_message(self):  # TC-02
        response = self.client.post(reverse("accounts:login"), {"username": "stud1", "password": "wrong-pw"})
        self.assertContains(response, "Invalid username or password.")


class DashboardTests(TestCase):
    """REQ-2: a different dashboard template per role."""

    def test_each_role_gets_its_own_template(self):
        for role in ("admin", "faculty", "student"):
            user = User.objects.create_user(username=f"{role}1", password="pw-123456", role=role)
            self.client.force_login(user)
            response = self.client.get(reverse("accounts:dashboard"))
            self.assertTemplateUsed(response, f"accounts/dashboard_{role}.html")
            self.client.logout()


def _admin_only_view(request):
    return "ok"


class RoleRequiredDecoratorTests(TestCase):
    """NFR-7, unit-tested directly: no admin-only page exists yet (ships with SEM-7),
    so this exercises role_required() itself rather than a real view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.student = User.objects.create_user(username="stud2", password="pw-123456", role="student")
        self.admin = User.objects.create_user(username="admin2", password="pw-123456", role="admin")
        self.view = role_required("admin")(_admin_only_view)

    def test_wrong_role_is_forbidden(self):
        request = self.factory.get("/whatever/")
        request.user = self.student
        with self.assertRaises(PermissionDenied):
            self.view(request)

    def test_matching_role_is_allowed(self):
        request = self.factory.get("/whatever/")
        request.user = self.admin
        self.assertEqual(self.view(request), "ok")


class StudentExcelUploadTests(TestCase):
    """SEM-8 (REQ-4): admin uploads students from Excel."""

    HEADER = ["SRN", "Name", "Email", "Phone", "Semester", "Section", "Department"]

    def setUp(self):
        self.admin = User.objects.create_user("adm", password="x", role="admin")
        self.url = reverse("accounts:upload_students")

    def xlsx(self, rows, header=None, name="students.xlsx"):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(header or self.HEADER)
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        return SimpleUploadedFile(name, buf.getvalue())

    def upload(self, rows, **kw):
        self.client.force_login(self.admin)
        return self.client.post(self.url, {"file": self.xlsx(rows, **kw)})

    def test_admin_only(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        for role in ("student", "faculty"):
            self.client.force_login(User.objects.create_user(f"u_{role}", password="x", role=role))
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_valid_rows_create_students_and_class(self):
        resp = self.upload([["PES1UG24CS001", "Asha Rao", "asha@pes.edu", 9876543210, 5, "c", "cse"]])
        self.assertEqual(len(resp.context["result"]["created"]), 1)
        u = User.objects.get(srn="PES1UG24CS001")
        self.assertEqual((u.role, u.first_name, u.last_name, u.phone), ("student", "Asha", "Rao", "9876543210"))
        self.assertTrue(u.check_password("PES1UG24CS001"))
        cls = u.classes.get()
        self.assertEqual((cls.department, cls.semester, cls.section), ("CSE", 5, "C"))

    def test_rejected_rows_listed_and_valid_rows_still_saved(self):  # acceptance criterion
        User.objects.create_user("taken", password="x", role="student", srn="PES1UG24CS003")
        resp = self.upload([
            ["PES1UG24CS001", "Good One", "g@pes.edu", None, 5, "C", "CSE"],
            ["PES1UG24CS002", "Bad Mail", "not-an-email", None, 5, "C", "CSE"],
            ["PES1UG24CS003", "Dup Db", "d@pes.edu", None, 5, "C", "CSE"],
            ["PES1UG24CS001", "Dup File", "f@pes.edu", None, 5, "C", "CSE"],
            ["PES1UG24CS004", "Bad Sem", "s@pes.edu", None, 9, "C", "CSE"],
            ["PES1UG24CS005", "Bad Phone", "p@pes.edu", "12345", 5, "C", "CSE"],
            ["PES1UG24CS006", "", "n@pes.edu", None, 5, "C", "CSE"],
        ])
        result = resp.context["result"]
        self.assertEqual([c[1] for c in result["created"]], ["PES1UG24CS001"])
        reasons = {row: reason for row, _, reason in result["rejected"]}
        self.assertEqual(sorted(reasons), [3, 4, 5, 6, 7, 8])  # Excel row numbers (header is row 1)
        self.assertIn("Email", reasons[3])
        self.assertIn("already registered", reasons[4])
        self.assertIn("Duplicate SRN", reasons[5])
        self.assertIn("Semester", reasons[6])
        self.assertIn("Phone", reasons[7])
        self.assertIn("Missing Name", reasons[8])
        self.assertContains(resp, "Rejected rows (6)")
        self.assertEqual(User.objects.filter(srn__startswith="PES1UG24CS00").count(), 2)

    def test_blank_rows_ignored(self):
        resp = self.upload([[None] * 7, ["PES1UG24CS001", "A B", "a@pes.edu", None, 1, "A", "CSE"]])
        self.assertEqual(len(resp.context["result"]["created"]), 1)
        self.assertEqual(resp.context["result"]["rejected"], [])

    def test_wrong_header_rejected(self):
        resp = self.upload([["x"]], header=["Roll", "Name"])
        self.assertContains(resp, "first row must be exactly")
        self.assertEqual(User.objects.filter(role="student").count(), 0)

    def test_non_xlsx_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {"file": SimpleUploadedFile("s.csv", b"a,b")})
        self.assertContains(resp, "Only .xlsx files")
        resp = self.client.post(self.url, {"file": SimpleUploadedFile("s.xlsx", b"not a workbook")})
        self.assertContains(resp, "Could not read the file")

    def test_no_file(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.post(self.url), "Choose an Excel")
