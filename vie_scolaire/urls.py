from django.urls import path

from . import views

app_name = "vie_scolaire"

urlpatterns = [
    path("retards/", views.retard_list, name="retard_list"),
    path("retards/declarer/", views.retard_declare, name="retard_declare"),
    path("retards/statistiques/", views.retard_stats, name="retard_stats"),
    path("retards/<int:retard_id>/justifier/", views.retard_justify, name="retard_justify"),
    path("retards/<int:retard_id>/valider/", views.retard_validate, name="retard_validate"),
    path("retards/eleves/<int:student_id>/", views.student_retards, name="student_retards"),
]
