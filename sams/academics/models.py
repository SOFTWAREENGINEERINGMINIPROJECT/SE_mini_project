from django.conf import settings
from django.db import models


class ClassSection(models.Model):
    department = models.CharField(max_length=5)
    semester = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=1)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="classes", blank=True)

    class Meta:
        unique_together = ("department", "semester", "section")

    def __str__(self):
        return f"{self.department} Sem{self.semester} {self.section}"


class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.code} - {self.name}"


class Teaching(models.Model):
    """faculty assigned to a subject for a class"""
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("subject", "class_section")

    def __str__(self):
        return f"{self.subject.code} / {self.class_section} / {self.faculty}"
