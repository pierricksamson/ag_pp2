from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.weekly_schedule, name="weekly"),
]