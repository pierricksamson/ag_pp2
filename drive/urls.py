from django.urls import path

from . import views

app_name = "drive"

urlpatterns = [
    path("", views.personal_drive, name="personal"),
    path("classe/<int:class_group_id>/", views.class_drive, name="class_drive"),
    path("fichiers/<int:file_id>/supprimer/", views.delete_file, name="delete_file"),
    path("quotas/", views.quota_settings, name="quota_settings"),
]