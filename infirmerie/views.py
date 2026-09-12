"""Vues de l'app infirmerie — passages à l'infirmerie, accès restreint."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from users.models import StudentProfile

from .models import InfirmerieVisit, VisitOutcome, VisitReason


def _can_manage(user) -> bool:
    """Seuls l'infirmier/l'infirmière et l'administration gèrent l'infirmerie."""
    return bool(user.is_authenticated and (user.is_nurse or user.is_admin))


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    if not _can_manage(request.user):
        raise PermissionDenied

    ongoing = InfirmerieVisit.objects.filter(departure_time__isnull=True).select_related("student__user", "student__class_group")
    today = timezone.localdate()
    today_visits = InfirmerieVisit.objects.filter(arrival_time__date=today).select_related("student__user", "student__class_group")

    students = (
        StudentProfile.objects.select_related("user", "class_group")
        .order_by("user__last_name", "user__first_name")
    )

    context = {
        "ongoing": ongoing,
        "today_visits": today_visits,
        "students": students,
        "reason_choices": VisitReason.choices,
        "outcome_choices": VisitOutcome.choices,
    }
    return render(request, "infirmerie/dashboard.html", context)


@login_required
@require_POST
def visit_create(request: HttpRequest) -> HttpResponse:
    if not _can_manage(request.user):
        raise PermissionDenied

    student_id = request.POST.get("student")
    reason = request.POST.get("reason") or VisitReason.AUTRE
    reason_detail = (request.POST.get("reason_detail") or "").strip()[:255]

    student = get_object_or_404(StudentProfile, id=student_id)
    if reason not in VisitReason.values:
        reason = VisitReason.AUTRE

    InfirmerieVisit.objects.create(
        student=student,
        reason=reason,
        reason_detail=reason_detail,
        recorded_by=request.user,
    )
    messages.success(request, f"Passage enregistré pour {student.user.get_full_name()}.")
    return redirect("infirmerie:dashboard")


@login_required
@require_POST
def visit_close(request: HttpRequest, visit_id: int) -> HttpResponse:
    if not _can_manage(request.user):
        raise PermissionDenied

    visit = get_object_or_404(InfirmerieVisit, id=visit_id)
    outcome = request.POST.get("outcome") or VisitOutcome.RETOUR_CLASSE
    care_given = (request.POST.get("care_given") or "").strip()[:1000]
    parent_notified = "parent_notified" in request.POST

    if outcome not in VisitOutcome.values:
        outcome = VisitOutcome.RETOUR_CLASSE

    visit.outcome = outcome
    visit.care_given = care_given
    visit.parent_notified = parent_notified
    visit.departure_time = timezone.now()
    visit.save(update_fields=["outcome", "care_given", "parent_notified", "departure_time"])
    messages.success(request, "Passage clôturé.")
    return redirect("infirmerie:dashboard")


@login_required
def student_visits(request: HttpRequest, student_id: int) -> HttpResponse:
    """Historique complet — réservé à l'infirmerie et à l'administration."""
    if not _can_manage(request.user):
        raise PermissionDenied

    student = get_object_or_404(StudentProfile.objects.select_related("user", "class_group"), id=student_id)
    visits = InfirmerieVisit.objects.filter(student=student).select_related("recorded_by")

    context = {
        "student": student,
        "visits": visits,
    }
    return render(request, "infirmerie/student_visits.html", context)