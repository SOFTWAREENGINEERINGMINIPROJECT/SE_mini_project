from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("my/", views.my_attendance, name="my"),
    path("class/", views.class_report, name="class"),
    path("class/export/<str:fmt>/", views.export_class_report, name="export"),
    path("shortage/", views.shortage_list, name="shortage"),
]