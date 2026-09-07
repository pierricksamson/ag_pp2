from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    path("redirect/", views.role_redirect, name="role_redirect"),

    path("dashboard/admin/", views.admin_dashboard, name="dashboard_admin"),
    path("dashboard/teacher/", views.teacher_dashboard, name="dashboard_teacher"),
    path("dashboard/student/", views.student_dashboard, name="dashboard_student"),
    path("dashboard/parent/", views.parent_dashboard, name="dashboard_parent"),
]