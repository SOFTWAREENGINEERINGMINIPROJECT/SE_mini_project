from django.conf import settings
from django.db import models
from academics.models import ClassSection, Subject


class AttendanceRecord(models.Model):
    STATUS = [("P", "Present"), ("A", "Absent"), ("L", "Leave")]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    date = models.DateField()
    hour = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=1, choices=STATUS, default="P")
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject", "date", "hour")  # REQ-9

    def __str__(self):
        return f"{self.student} {self.subject.code} {self.date} h{self.hour}: {self.status}"


class AttendanceLog(models.Model):
    """every change to a record (NFR-11)"""
    record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=1)
    new_status = models.CharField(max_length=1)
    changed_at = models.DateTimeField(auto_now_add=True)
