from django.conf import settings
from django.db import models


class LeaveRequest(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} {self.from_date} to {self.to_date} ({self.status})"


class ShortageAlert(models.Model):
    """log of shortage mails sent (SEM-20), so the same student isn't mailed after every class"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE)
    percent = models.FloatField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} {self.subject.code} {self.percent}% ({self.sent_at:%d %b %Y})"
