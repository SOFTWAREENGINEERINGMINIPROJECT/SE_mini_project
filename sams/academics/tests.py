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
