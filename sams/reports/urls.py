from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("my/", views.my_attendance, name="my"),
]