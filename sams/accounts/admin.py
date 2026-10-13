from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("SAMS", {"fields": ("role", "srn", "phone")}),)
    list_display = ("username", "first_name", "role", "srn", "email")
    list_filter = ("role",)
