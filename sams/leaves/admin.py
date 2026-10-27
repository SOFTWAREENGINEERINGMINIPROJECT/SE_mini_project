from django.contrib import admin
from .models import LeaveRequest

admin.site.register(LeaveRequest)
from .models import ShortageAlert

admin.site.register(ShortageAlert)
