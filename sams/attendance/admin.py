from django.contrib import admin
from .models import AttendanceLog, AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "date", "hour", "status")
    list_filter = ("subject", "date", "status")


admin.site.register(AttendanceLog)
