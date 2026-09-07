from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="users:login", permanent=False)),
    path("", include("users.urls", namespace="users")),
    path("academics/", include("academics.urls", namespace="academics")),
    path("schedule/", include("schedule.urls", namespace="schedule")),
]