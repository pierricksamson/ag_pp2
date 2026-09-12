from django.contrib import admin

from .models import InfirmerieVisit


@admin.register(InfirmerieVisit)
class InfirmerieVisitAdmin(admin.ModelAdmin):
    list_display = ("student", "arrival_time", "departure_time", "reason", "outcome", "recorded_by")
    list_filter = ("reason", "outcome", "parent_notified")
    search_fields = ("student__user__first_name", "student__user__last_name", "student__student_number")
    autocomplete_fields = ("student", "recorded_by")
    date_hierarchy = "arrival_time"