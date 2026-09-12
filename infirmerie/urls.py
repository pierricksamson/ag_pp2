from django.urls import path

from . import views

app_name = "infirmerie"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("ajouter/", views.visit_create, name="visit_create"),
    path("<int:visit_id>/cloturer/", views.visit_close, name="visit_close"),
    path("eleves/<int:student_id>/", views.student_visits, name="student_visits"),
]