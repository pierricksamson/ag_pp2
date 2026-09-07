from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AdminProfile, ParentProfile, StudentProfile, TeacherProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("last_name", "first_name")
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name", "phone")
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Identité",
            {"fields": ("first_name", "last_name", "phone", "role")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Dates importantes",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                        "password1",
                        "password2",
                    ),
            },
        ),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_number", "hire_date")
    search_fields = ("user__email", "user__last_name", "user__first_name", "employee_number")
    autocomplete_fields = ("user",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_number", "class_group", "birth_date")
    list_filter = ("class_group",)
    search_fields = ("user__email", "user__last_name", "user__first_name", "student_number")
    autocomplete_fields = ("user", "parents")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "relation", "occupation")
    list_filter = ("relation",)
    search_fields = ("user__email", "user__last_name", "user__first_name")
    autocomplete_fields = ("user",)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    search_fields = ("user__email", "user__last_name", "user__first_name")
    autocomplete_fields = ("user",)