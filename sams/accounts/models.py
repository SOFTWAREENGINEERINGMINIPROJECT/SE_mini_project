from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [("admin", "Admin"), ("faculty", "Faculty"), ("student", "Student")]
    role = models.CharField(max_length=10, choices=ROLES, default="student")
    srn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        # `createsuperuser` makes a superuser with the default role "student", which then lands on the
        # student dashboard. A superuser is always an SAMS admin.
        if self.is_superuser:
            self.role = "admin"
        # SAMS admins manage users, subjects and classes through the Django admin site (REQ-3, REQ-5..7),
        # so they need staff + full permissions there.
        if self.role == "admin":
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.srn or self.username
