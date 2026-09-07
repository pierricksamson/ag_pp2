from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from schedule.models import CourseSession
from users.models import StudentProfile

from .models import AbsenceJustification, AttendanceRecord, AttendanceStatus


# ---------- Helpers ----------


def _session_students(session: CourseSession):
    return (
        StudentProfile.objects.filter(class_group__in=session.class_groups.all())
        .select_related("user", "class_group")
        .order_by("user__last_name", "user__first_name")
        .distinct()
    )


def _ensure_records(session: CourseSession) -> None:
    """Crée les feuilles de présence manquantes pour tous les élèves de la séance."""
    existing_ids = set(session.attendances.values_list("student_id", flat=True))
    to_create = [
        AttendanceRecord(student=s, session=session, status=AttendanceStatus.PRESENT)
        for s in _session_students(session)
        if s.id not in existing_ids
    ]
    if to_create:
        AttendanceRecord.objects.bulk_create(to_create)


def _stats(session: CourseSession) -> dict:
    qs = session.attendances.all()
    total = qs.count()
    present = qs.filter(status=AttendanceStatus.PRESENT).count()
    absent = qs.filter(status=AttendanceStatus.ABSENT).count()
    late = qs.filter(status=AttendanceStatus.LATE).count()
    excused = qs.filter(status=AttendanceStatus.EXCUSED).count()
    rate = round(100 * present / total, 1) if total else 0.0
    return {
        "total": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_rate": rate,
    }


def _parse_payload(post) -> tuple[str, int, str]:
    status = (post.get("status") or "").strip().upper()
    if status not in AttendanceStatus.values:
        status = AttendanceStatus.PRESENT
    try:
        minutes_late = int(post.get("minutes_late") or 0)
    except ValueError:
        minutes_late = 0
    reason = (post.get("reason") or "").strip()[:255]
    return status, max(minutes_late, 0), reason


def _can_manage(user, session: CourseSession) -> bool:
    if user.is_admin:
        return True
    teacher_profile = getattr(user, "teacher_profile", None)
    return bool(user.is_teacher and teacher_profile and session.teacher_id == teacher_profile.id)


# ---------- Prof : faire l'appel ----------


@login_required
def take_attendance(request: HttpRequest, session_id: int) -> HttpResponse:
    session = get_object_or_404(
        CourseSession.objects.select_related("subject", "teacher__user", "room").prefetch_related("class_groups"),
        id=session_id,
    )
    if not _can_manage(request.user, session):
        raise PermissionDenied

    _ensure_records(session)
    records = (
        session.attendances
        .select_related("student__user")
        .order_by("student__user__last_name", "student__user__first_name")
    )

    if request.method == "POST":
        with transaction.atomic():
            saved = 0
            for r in records:
                status, minutes_late, reason = _parse_payload({
                    "status": request.POST.get(f"status_{r.id}", ""),
                    "minutes_late": request.POST.get(f"minutes_late_{r.id}", "0"),
                    "reason": request.POST.get(f"reason_{r.id}", ""),
                })
                r.status = status
                r.minutes_late = minutes_late if status == AttendanceStatus.LATE else 0
                r.reason = reason
                r.recorded_by = getattr(request.user, "teacher_profile", None)
                r.save(update_fields=["status", "minutes_late", "reason", "recorded_by"])
                saved += 1
        messages.success(request, f"Appel enregistré pour {saved} élève(s).")
        return redirect("attendance:take_attendance", session_id=session.id)

    context = {
        "session": session,
        "records": records,
        "status_choices": AttendanceStatus.choices,
        "stats": _stats(session),
    }
    return render(request, "attendance/take.html", context)


# ---------- API : sauvegarde AJAX d'une ligne ----------


@login_required
@require_POST
def attendance_save_ajax(request: HttpRequest, record_id: int) -> JsonResponse:
    record = get_object_or_404(
        AttendanceRecord.objects.select_related("session", "student__user"),
        id=record_id,
    )
    if not _can_manage(request.user, record.session):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    status, minutes_late, reason = _parse_payload(request.POST)
    record.status = status
    record.minutes_late = minutes_late if status == AttendanceStatus.LATE else 0
    record.reason = reason
    record.recorded_by = getattr(request.user, "teacher_profile", None)
    record.save(update_fields=["status", "minutes_late", "reason", "recorded_by"])

    return JsonResponse({
        "ok": True,
        "record": {
            "id": record.id,
            "status": record.status,
            "minutes_late": record.minutes_late,
            "reason": record.reason,
        },
        "stats": _stats(record.session),
    })


@login_required
@require_POST
def attendance_save_all(request: HttpRequest, session_id: int) -> HttpResponse:
    """Sauvegarde bulk (fallback sans JS + bouton « Sauvegarder tout »)."""
    session = get_object_or_404(CourseSession, id=session_id)
    if not _can_manage(request.user, session):
        raise PermissionDenied

    records = session.attendances.all()
    with transaction.atomic():
        saved = 0
        for r in records:
            status, minutes_late, reason = _parse_payload({
                "status": request.POST.get(f"status_{r.id}", ""),
                "minutes_late": request.POST.get(f"minutes_late_{r.id}", "0"),
                "reason": request.POST.get(f"reason_{r.id}", ""),
            })
            r.status = status
            r.minutes_late = minutes_late if status == AttendanceStatus.LATE else 0
            r.reason = reason
            r.recorded_by = getattr(request.user, "teacher_profile", None)
            r.save(update_fields=["status", "minutes_late", "reason", "recorded_by"])
            saved += 1

    messages.success(request, f"{saved} présence(s) enregistrée(s).")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "saved": saved, "stats": _stats(session)})
    return redirect("attendance:take_attendance", session_id=session.id)


# ---------- Élève / Parent : justification d'absence ----------


@login_required
@require_POST
def justify_absence(request: HttpRequest, record_id: int) -> HttpResponse:
    record = get_object_or_404(AttendanceRecord.objects.select_related("student__user"), id=record_id)

    is_owner = request.user.is_student and getattr(request.user, "student_profile", None) == record.student
    is_parent_of = (
        request.user.is_parent
        and record.student in request.user.parent_profile.children.all()
    )
    if not (is_owner or is_parent_of or request.user.is_admin):
        raise PermissionDenied

    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Merci de préciser un motif de justification.")
    else:
        AbsenceJustification.objects.create(
            attendance=record, submitted_by=request.user, reason=reason[:1000]
        )
        messages.success(request, "Justification envoyée, en attente de validation.")
    return redirect("attendance:student_absences", student_id=record.student_id)


@login_required
@require_POST
def review_justification(request: HttpRequest, justification_id: int) -> HttpResponse:
    justification = get_object_or_404(
        AbsenceJustification.objects.select_related("attendance__session"), id=justification_id
    )
    if not _can_manage(request.user, justification.attendance.session):
        raise PermissionDenied

    decision = request.POST.get("decision")
    justification.reviewed_by = request.user
    justification.reviewed_at = timezone.now()
    if decision == "approve":
        justification.status = AbsenceJustification.Status.APPROVED
        justification.attendance.justified = True
        justification.attendance.justification_reason = justification.reason
        justification.attendance.save(update_fields=["justified", "justification_reason"])
        messages.success(request, "Justification approuvée.")
    else:
        justification.status = AbsenceJustification.Status.REJECTED
        messages.info(request, "Justification rejetée.")
    justification.save(update_fields=["status", "reviewed_by", "reviewed_at"])

    return redirect("attendance:take_attendance", session_id=justification.attendance.session_id)


# ---------- Élève / Parent : historique des absences ----------


def _resolve_student(request: HttpRequest, student_id: int) -> StudentProfile:
    student = get_object_or_404(StudentProfile.objects.select_related("user", "class_group"), id=student_id)
    if request.user.is_admin:
        return student
    if request.user.is_student and getattr(request.user, "student_profile", None) == student:
        return student
    if request.user.is_parent and student in request.user.parent_profile.children.all():
        return student
    raise PermissionDenied


@login_required
def student_absences(request: HttpRequest, student_id: int) -> HttpResponse:
    student = _resolve_student(request, student_id)
    records = (
        AttendanceRecord.objects.filter(student=student)
        .select_related("session__subject", "session__teacher__user")
        .prefetch_related("justifications")
        .order_by("-recorded_at")
    )

    children = []
    if request.user.is_parent:
        children = list(request.user.parent_profile.children.select_related("user"))

    context = {
        "student": student,
        "records": records,
        "children": children,
        "can_justify": request.user.is_student or request.user.is_parent,
    }
    return render(request, "attendance/student_absences.html", context)
