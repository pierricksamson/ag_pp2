from django.contrib import admin

from .models import CourseSession, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "location")
    search_fields = ("name", "location")


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "day",
        "start_time",
        "end_time",
        "teacher",
        "room",
        "display_classes",
    )
    list_filter = ("day", "teacher", "subject", "room")
    search_fields = ("subject__name", "subject__code", "teacher__user__last_name", "room__name")
    filter_horizontal = ("class_groups",)

    @admin.display(description="Classes")
    def display_classes(self, obj):
        return ", ".join(str(g) for g in obj.class_groups.all()) or "—"