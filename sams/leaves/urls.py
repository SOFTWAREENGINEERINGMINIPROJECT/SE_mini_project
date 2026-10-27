from django.urls import path

from . import views

app_name = "leaves"

urlpatterns = [
    path("apply/", views.apply_leave, name="apply"),
    path("my/", views.my_leaves, name="my"),
]
