from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("sessions/<int:session_id>/take/", views.take_attendance, name="take_attendance"),
    path("api/record/<int:record_id>/save/", views.attendance_save_ajax, name="attendance_save_ajax"),
    path("api/session/<int:session_id>/save_all/", views.attendance_save_all, name="attendance_save_all"),
    path("records/<int:record_id>/justify/", views.justify_absence, name="justify_absence"),
    path("justifications/<int:justification_id>/review/", views.review_justification, name="review_justification"),
    path("students/<int:student_id>/absences/", views.student_absences, name="student_absences"),
]