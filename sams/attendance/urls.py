from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("mark/", views.mark_attendance, name="mark"),
    path("edit/", views.edit_attendance, name="edit"),
]
