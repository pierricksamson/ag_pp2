from django.contrib import admin

from .models import (
    AcademicYear,
    ClassGroup,
    Evaluation,
    Grade,
    Level,
    Subject,
    Term,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("label", "start_date", "end_date", "is_current")


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "level")
    list_filter = ("level",)
    search_fields = ("code", "name")


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "academic_year")
    list_filter = ("academic_year", "level")


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "start_date", "end_date", "is_current")
    list_filter = ("academic_year", "is_current")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "class_group", "term", "date", "coefficient")
    list_filter = ("term", "subject", "class_group")
    search_fields = ("title",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("evaluation", "student", "value", "status")
    list_filter = ("status", "evaluation__term", "evaluation__subject")