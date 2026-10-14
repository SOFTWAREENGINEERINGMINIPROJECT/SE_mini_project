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
