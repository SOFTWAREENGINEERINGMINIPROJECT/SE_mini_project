from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [("admin", "Admin"), ("faculty", "Faculty"), ("student", "Student")]
    role = models.CharField(max_length=10, choices=ROLES, default="student")
    srn = models.CharField(max_length=13, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.srn or self.username
