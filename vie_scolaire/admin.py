from django.contrib import admin

from .models import Retard


@admin.register(Retard)
class RetardAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "duration_minutes", "motif", "status", "declared_by", "validated_by")
    list_filter = ("status", "motif", "date")
    search_fields = ("student__user__first_name", "student__user__last_name", "student__student_number")
    autocomplete_fields = ("student", "declared_by", "validated_by")
    date_hierarchy = "date"
