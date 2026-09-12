from django.contrib import admin

from .forms import CourseSessionForm
from .models import CourseSession, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display        = ("name", "capacity", "location")
    search_fields       = ("name", "location")
    list_filter         = ("location",)
    ordering            = ("location", "name")


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    form = CourseSessionForm
    list_display        = ("subject", "day", "start_time", "end_time", "teacher", "room", "display_classes")
    list_filter         = ("day", "teacher", "subject", "room")
    search_fields       = ("subject__name", "subject__code", "teacher__user__first_name", "teacher__user__last_name", "room__name")
    filter_horizontal   = ("class_groups",)
    list_select_related = ("subject", "teacher", "room")
    ordering            = ("day", "start_time")

    def get_queryset(self, request):
        return (super().get_queryset(request).prefetch_related("class_groups"))

    @admin.display(description="Classes")
    def display_classes(self, obj):
        return ", ".join(str(group) for group in obj.class_groups.all()) or "—"
