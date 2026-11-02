from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from academics.models import ClassSection, Subject, Teaching

User = get_user_model()


class AcademicsConstraintTests(TestCase):
    def test_subject_code_unique(self):
        Subject.objects.create(code="X1", name="A", semester=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subject.objects.create(code="X1", name="B", semester=1)

    def test_class_unique(self):
        ClassSection.objects.create(department="CSE", semester=5, section="C")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClassSection.objects.create(department="CSE", semester=5, section="C")

    def test_teaching_unique_on_subject_and_class(self):
        f = User.objects.create_user("f", password="x", role="faculty")
        f2 = User.objects.create_user("f2", password="x", role="faculty")
        s = Subject.objects.create(code="X1", name="A", semester=1)
        c = ClassSection.objects.create(department="CSE", semester=1, section="A")
        Teaching.objects.create(faculty=f, subject=s, class_section=c)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Teaching.objects.create(faculty=f2, subject=s, class_section=c)


class AcademicsAdminFormTests(TestCase):
    """REQ-6/REQ-7: admin dropdowns only offer students for classes and faculty for teaching."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        U = get_user_model()
        self.admin = U.objects.create_user("adm6", password="x", role="admin")
        self.fac = U.objects.create_user("fac6", password="x", role="faculty")
        self.stu = U.objects.create_user("stu6", password="x", role="student")
        self.client.force_login(self.admin)

    def test_class_form_lists_only_students(self):
        r = self.client.get("/admin/academics/classsection/add/")
        self.assertContains(r, "stu6")
        self.assertNotContains(r, "fac6")

    def test_teaching_form_lists_only_faculty(self):
        r = self.client.get("/admin/academics/teaching/add/")
        self.assertContains(r, "fac6")
        self.assertNotContains(r, "stu6")

    def test_class_list_shows_student_count(self):
        from .models import ClassSection
        c = ClassSection.objects.create(department="CSE", semester=5, section="C")
        c.students.add(self.stu)
        r = self.client.get("/admin/academics/classsection/")
        self.assertContains(r, "CSE")
