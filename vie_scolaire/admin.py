from django.contrib import admin

from .models import Observation, Retard


@admin.register(Retard)
class RetardAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "duration_minutes", "motif", "status", "source", "declared_by", "validated_by")
    list_filter = ("status", "motif", "source", "date")
    search_fields = ("student__user__first_name", "student__user__last_name", "student__student_number")
    autocomplete_fields = ("student", "declared_by", "validated_by")
    date_hierarchy = "date"


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("student", "type", "subject", "author", "created_at")
    list_filter = ("type", "subject")
    search_fields = ("student__user__first_name", "student__user__last_name", "title", "description")
    autocomplete_fields = ("student", "subject", "author")
    date_hierarchy = "created_at"