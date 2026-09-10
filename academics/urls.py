from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("etablissement/", views.establishment_management, name="establishment_management"),
    path("evaluations/", views.evaluation_list, name="evaluation_list"),
    path("evaluations/create/", views.evaluation_create, name="evaluation_create"),
    path("evaluations/<int:evaluation_id>/entry/", views.evaluation_entry, name="evaluation_entry"),
    path("evaluations/<int:evaluation_id>/save/", views.evaluation_save_all, name="evaluation_save_all"),
    path("api/grade/<int:grade_id>/save/", views.grade_save_ajax, name="grade_save_ajax"),
    path("grades/", views.grades_view, name="grades"),
]