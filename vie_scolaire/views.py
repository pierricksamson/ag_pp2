from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from academics.models import ClassGroup
from users.models import StudentProfile

from .models import Observation, ObservationType, Retard, RetardMotif, RetardStatus


# ---------- Helpers ----------


def _can_manage(user) -> bool:
    """Déclaration/validation des retards : réservé au personnel (professeurs, admin/vie scolaire)."""
    return bool(user.is_authenticated and user.is_staff_member)


def _resolve_student(request: HttpRequest, student_id: int) -> StudentProfile:
    student = get_object_or_404(StudentProfile.objects.select_related("user", "class_group"), id=student_id)
    if request.user.is_staff_member:
        return student
    if request.user.is_student and getattr(request.user, "student_profile", None) == student:
        return student
    if request.user.is_parent and student in request.user.parent_profile.children.all():
        return student
    raise PermissionDenied


# ---------- Déclarer un retard ----------


@login_required
def retard_declare(request: HttpRequest) -> HttpResponse:
    if not _can_manage(request.user):
        raise PermissionDenied

    if request.method == "POST":
        student_id = request.POST.get("student")
        date = request.POST.get("date") or timezone.localdate()
        duration = request.POST.get("duration_minutes") or 0
        motif = request.POST.get("motif") or RetardMotif.AUTRE
        motif_detail = (request.POST.get("motif_detail") or "").strip()[:255]

        student = get_object_or_404(StudentProfile, id=student_id)
        try:
            duration = max(1, int(duration))
        except ValueError:
            duration = 5
        if motif not in RetardMotif.values:
            motif = RetardMotif.AUTRE

        Retard.objects.create(
            student=student,
            date=date,
            duration_minutes=duration,
            motif=motif,
            motif_detail=motif_detail,
            declared_by=request.user,
        )
        messages.success(request, f"Retard déclaré pour {student.user.get_full_name()}.")
        return redirect("vie_scolaire:retard_list")

    students = (
        StudentProfile.objects.select_related("user", "class_group")
        .order_by("user__last_name", "user__first_name")
    )
    context = {
        "students": students,
        "motif_choices": RetardMotif.choices,
        "today": timezone.localdate(),
    }
    return render(request, "vie_scolaire/retard_form.html", context)


# ---------- Historique ----------


@login_required
def retard_list(request: HttpRequest) -> HttpResponse:
    qs = Retard.objects.select_related("student__user", "student__class_group", "declared_by", "validated_by")

    if request.user.is_staff_member:
        class_id = request.GET.get("class_group")
        status = request.GET.get("status")
        student_id = request.GET.get("student")
        if class_id:
            qs = qs.filter(student__class_group_id=class_id)
        if status in RetardStatus.values:
            qs = qs.filter(status=status)
        if student_id:
            qs = qs.filter(student_id=student_id)
        class_groups = ClassGroup.objects.order_by("name")
    elif request.user.is_student:
        student = getattr(request.user, "student_profile", None)
        qs = qs.filter(student=student) if student else qs.none()
        class_groups = []
    elif request.user.is_parent:
        children = list(request.user.parent_profile.children.all())
        qs = qs.filter(student__in=children)
        class_groups = []
    else:
        qs = qs.none()
        class_groups = []

    context = {
        "retards": qs[:300],
        "class_groups": class_groups,
        "status_choices": RetardStatus.choices,
        "can_manage": request.user.is_staff_member,
        "filters": {
            "class_group": request.GET.get("class_group", ""),
            "status": request.GET.get("status", ""),
            "student": request.GET.get("student", ""),
        },
    }
    return render(request, "vie_scolaire/retard_list.html", context)


@login_required
def student_retards(request: HttpRequest, student_id: int) -> HttpResponse:
    student = _resolve_student(request, student_id)
    retards = Retard.objects.filter(student=student).select_related("declared_by", "validated_by")

    children = []
    if request.user.is_parent:
        children = list(request.user.parent_profile.children.select_related("user"))

    context = {
        "student": student,
        "retards": retards,
        "children": children,
        "can_justify": request.user.is_student or request.user.is_parent,
    }
    return render(request, "vie_scolaire/student_retards.html", context)


# ---------- Justification (élève / parent) ----------


@login_required
@require_POST
def retard_justify(request: HttpRequest, retard_id: int) -> HttpResponse:
    retard = get_object_or_404(Retard.objects.select_related("student"), id=retard_id)

    is_owner = request.user.is_student and getattr(request.user, "student_profile", None) == retard.student
    is_parent_of = request.user.is_parent and retard.student in request.user.parent_profile.children.all()
    if not (is_owner or is_parent_of or request.user.is_staff_member):
        raise PermissionDenied

    justification = (request.POST.get("justification") or "").strip()
    if not justification:
        messages.error(request, "Merci de préciser une justification.")
    else:
        retard.justification = justification[:1000]
        retard.justification_submitted_at = timezone.now()
        retard.save(update_fields=["justification", "justification_submitted_at"])
        messages.success(request, "Justification envoyée, en attente de validation.")
    return redirect("vie_scolaire:student_retards", student_id=retard.student_id)


# ---------- Validation (professeur / vie scolaire) ----------


@login_required
@require_POST
def retard_validate(request: HttpRequest, retard_id: int) -> HttpResponse:
    retard = get_object_or_404(Retard, id=retard_id)
    if not _can_manage(request.user):
        raise PermissionDenied

    decision = request.POST.get("decision")
    retard.validated_by = request.user
    retard.validated_at = timezone.now()
    if decision == "justify":
        retard.status = RetardStatus.JUSTIFIED
        messages.success(request, "Retard marqué comme justifié.")
    else:
        retard.status = RetardStatus.UNJUSTIFIED
        messages.info(request, "Retard marqué comme non justifié.")
    retard.save(update_fields=["status", "validated_by", "validated_at"])

    return redirect(request.POST.get("next") or "vie_scolaire:retard_list")


# ---------- Statistiques ----------
# ---------- Tableau de bord professeur ----------


def _teacher_classes(teacher_profile):
    """Classes suivies par le prof (affectation explicite, sinon déduites de son emploi du temps)."""
    if teacher_profile is None:
        return ClassGroup.objects.none()
    assigned = teacher_profile.class_groups.all()
    if assigned.exists():
        return assigned
    return ClassGroup.objects.filter(sessions__teacher=teacher_profile).distinct()


@login_required
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    """Tableau de bord vie scolaire du professeur, façon Pronote : retards, observations, infirmerie."""
    if not request.user.is_teacher:
        raise PermissionDenied

    teacher = getattr(request.user, "teacher_profile", None)
    classes = _teacher_classes(teacher)
    students = StudentProfile.objects.filter(class_group__in=classes).select_related("user", "class_group")

    retards = (
        Retard.objects.filter(student__in=students)
        .select_related("student__user", "student__class_group")
        .order_by("-date", "-created_at")[:20]
    )
    observations = (
        Observation.objects.filter(student__in=students)
        .select_related("student__user", "subject", "author")
        .order_by("-created_at")[:20]
    )

    # On ne remonte qu'un indicateur (nom + heure) : le détail médical reste
    # réservé à l'infirmerie et à l'administration.
    infirmerie_flags = []
    try:
        from infirmerie.models import InfirmerieVisit
        infirmerie_flags = list(
            InfirmerieVisit.objects.filter(student__in=students)
            .values("student__user__first_name", "student__user__last_name", "arrival_time")
            .order_by("-arrival_time")[:10]
        )
    except Exception:
        infirmerie_flags = []

    context = {
        "classes": classes,
        "students": students,
        "retards": retards,
        "observations": observations,
        "infirmerie_flags": infirmerie_flags,
        "motif_choices": RetardMotif.choices,
        "observation_types": ObservationType.choices,
        "pending_retards_count": Retard.objects.filter(student__in=students, status=RetardStatus.PENDING).count(),
    }
    return render(request, "vie_scolaire/teacher_dashboard.html", context)


@login_required
def observation_create(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        raise PermissionDenied
    if not (request.user.is_teacher or request.user.is_admin):
        raise PermissionDenied

    student_id = request.POST.get("student")
    obs_type = request.POST.get("type") or ObservationType.NOTE
    subject_id = request.POST.get("subject") or None
    title = (request.POST.get("title") or "").strip()[:120]
    description = (request.POST.get("description") or "").strip()[:1000]

    student = get_object_or_404(StudentProfile, id=student_id)
    if obs_type not in ObservationType.values:
        obs_type = ObservationType.NOTE

    Observation.objects.create(
        student=student,
        type=obs_type,
        subject_id=subject_id if subject_id else None,
        title=title,
        description=description,
        author=request.user,
    )
    messages.success(request, f"Observation ajoutée pour {student.user.get_full_name()}.")
    return redirect("vie_scolaire:teacher_dashboard")

@login_required
def retard_stats(request: HttpRequest) -> HttpResponse:
    if not _can_manage(request.user):
        raise PermissionDenied

    qs = Retard.objects.all()
    total = qs.count()
    pending = qs.filter(status=RetardStatus.PENDING).count()
    justified = qs.filter(status=RetardStatus.JUSTIFIED).count()
    unjustified = qs.filter(status=RetardStatus.UNJUSTIFIED).count()
    avg_duration = qs.aggregate(avg=Avg("duration_minutes"))["avg"] or 0

    by_class = (
        qs.values("student__class_group__name")
        .annotate(count=Count("id"), avg_duration=Avg("duration_minutes"))
        .order_by("-count")
    )
    motif_labels = dict(RetardMotif.choices)
    by_motif = [
        {"label": motif_labels.get(row["motif"], row["motif"]), "count": row["count"]}
        for row in qs.values("motif").annotate(count=Count("id")).order_by("-count")
    ]
    top_students = (
        qs.values("student__id", "student__user__first_name", "student__user__last_name")
        .annotate(count=Count("id"), total_minutes=Sum("duration_minutes"))
        .order_by("-count")[:10]
    )

    context = {
        "total": total,
        "pending": pending,
        "justified": justified,
        "unjustified": unjustified,
        "avg_duration": round(avg_duration, 1),
        "by_class": by_class,
        "by_motif": by_motif,
        "top_students": top_students,
    }
    return render(request, "vie_scolaire/retard_stats.html", context)
