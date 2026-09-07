from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Max, Min, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from users.models import Role, StudentProfile, TeacherProfile

from .models import (
    ClassGroup,
    Evaluation,
    Grade,
    Subject,
    Term,
)
from .services import (
    class_subject_average,
    subject_average,
    weighted_average,
)


# ---------- Prof : création d'évaluation ----------


@login_required
def evaluation_create(request: HttpRequest) -> HttpResponse:
    if not request.user.is_teacher:
        raise PermissionDenied

    teacher = request.user.teacher_profile
    # matières enseignées ; si aucune, on montre toutes
    subjects = teacher.subjects.all() if teacher else Subject.objects.none()
    if not subjects.exists():
        subjects = Subject.objects.all()

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        subject_id = request.POST.get("subject")
        class_group_id = request.POST.get("class_group")
        term_id = request.POST.get("term")
        eval_date = request.POST.get("date") or str(date.today())
        coefficient = request.POST.get("coefficient") or "1"
        max_grade_input = request.POST.get("scale_max") or "20"

        errors = []
        if not title:
            errors.append("Le titre est obligatoire.")
        if not subject_id:
            errors.append("La matière est obligatoire.")
        if not class_group_id:
            errors.append("La classe est obligatoire.")
        if not term_id:
            errors.append("Le trimestre est obligatoire.")
        try:
            coefficient_v = float(coefficient)
            scale_max_v = float(max_grade_input)
        except ValueError:
            errors.append("Coefficient et note max doivent etre numeriques.")
            coefficient_v = 1
            scale_max_v = 20

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            evaluation = Evaluation.objects.create(
                title=title,
                subject_id=int(subject_id),
                class_group_id=int(class_group_id),
                term_id=int(term_id),
                teacher=teacher,
                date=eval_date,
                coefficient=coefficient_v,
                scale_max=scale_max_v,
            )
            # Pré-créer une ligne Grade par élève de la classe (statut PRESENT, valeur nulle).
            students = StudentProfile.objects.filter(class_group_id=int(class_group_id))
            Grade.objects.bulk_create([
                Grade(evaluation=evaluation, student=s, status=Grade.Status.PRESENT)
                for s in students
            ])
            messages.success(request, "Évaluation créée. Vous pouvez maintenant saisir les notes.")
            return redirect("academics:evaluation_entry", evaluation_id=evaluation.id)

    context = {
        "subjects": subjects.order_by("name"),
        "class_groups": ClassGroup.objects.select_related("level", "academic_year").order_by("level__order", "name"),
        "terms": Term.objects.select_related("academic_year").order_by("-is_current", "start_date"),
        "today": date.today().isoformat(),
    }
    return render(request, "academics/evaluation_create.html", context)


# ---------- Prof : saisie matricielle ----------


@login_required
def evaluation_entry(request: HttpRequest, evaluation_id: int) -> HttpResponse:
    if not request.user.is_teacher:
        raise PermissionDenied

    evaluation = get_object_or_404(
        Evaluation.objects.select_related("subject", "class_group", "term", "teacher"),
        id=evaluation_id,
    )

    grades = (
        evaluation.grades
        .select_related("student__user")
        .order_by("student__user__last_name", "student__user__first_name")
    )

    if request.method == "POST":
        with transaction.atomic():
            saved = 0
            for g in grades:
                value_raw = request.POST.get(f"value_{g.id}")
                status_raw = request.POST.get(f"status_{g.id}") or Grade.Status.PRESENT
                if value_raw is None or value_raw == "":
                    g.value = None
                    # Si pas de valeur → PRESENT par défaut, sinon statut choisi
                    g.status = status_raw if status_raw in Grade.Status.values else Grade.Status.PRESENT
                else:
                    try:
                        v = float(value_raw)
                    except ValueError:
                        v = None
                    g.value = v
                    if v is not None:
                        g.status = Grade.Status.PRESENT
                    else:
                        g.status = status_raw
                g.save()
                saved += 1
        messages.success(request, f"{saved} note(s) enregistrée(s).")
        return redirect("academics:evaluation_entry", evaluation_id=evaluation.id)

    context = {
        "evaluation": evaluation,
        "grades": grades,
        "status_choices": Grade.Status.choices,
        "stats": {
            "average": evaluation.average,
            "min": evaluation.min_grade,
            "max": evaluation.scale_max,
            "attendance_rate": evaluation.attendance_rate,
            "present": evaluation.count_present,
            "total": evaluation.count_total,
        },
    }
    return render(request, "academics/evaluation_entry.html", context)


# ---------- Prof : liste ----------


@login_required
def evaluation_list(request: HttpRequest) -> HttpResponse:
    if not request.user.is_teacher:
        raise PermissionDenied

    teacher = request.user.teacher_profile
    qs = (
        Evaluation.objects
        .filter(teacher=teacher)
        .select_related("subject", "class_group", "term")
        .order_by("-date")
    )
    return render(request, "academics/evaluation_list.html", {"evaluations": qs})


# ---------- Élève / Parent : relevé de notes ----------


def _resolve_student(request: HttpRequest) -> StudentProfile | None:
    """Récupère le StudentProfile de l'élève connecté ou de l'enfant sélectionné (parent)."""
    if request.user.is_student:
        return getattr(request.user, "student_profile", None)
    if request.user.is_parent:
        children = list(request.user.parent_profile.children.select_related("user", "class_group"))
        if not children:
            return None
        sel = request.GET.get("child")
        if sel:
            for c in children:
                if str(c.id) == sel:
                    return c
        return children[0]
    return None


@login_required
def grades_view(request: HttpRequest) -> HttpResponse:
    if not (request.user.is_student or request.user.is_parent):
        raise PermissionDenied

    student = _resolve_student(request)
    if student is None:
        return render(request, "academics/grades.html", {
            "no_profile": True,
            "children": list(request.user.parent_profile.children.select_related("user")) if request.user.is_parent else [],
        })

    terms = Term.objects.select_related("academic_year").order_by("-start_date")
    current_term = terms.filter(is_current=True).first() or terms.first()
    selected_term_id = request.GET.get("term")
    term = current_term
    if selected_term_id:
        try:
            term = terms.get(id=int(selected_term_id))
        except (ValueError, Term.DoesNotExist):
            pass

    # Toutes les notes du trimestre pour l'élève
    grades_qs = (
        Grade.objects
        .filter(student=student, evaluation__term=term)
        .select_related("evaluation__subject", "evaluation__class_group")
        .order_by("evaluation__subject__name", "-evaluation__date")
    )

    # Stats par matière
    subjects_data = []
    subjects_seen = set()
    for g in grades_qs:
        subj = g.evaluation.subject
        if subj.id in subjects_seen:
            continue
        subjects_seen.add(subj.id)

        subj_grades = [x for x in grades_qs if x.evaluation.subject_id == subj.id]
        student_avg = subject_average(student, term, subj)
        class_avg = class_subject_average(student.class_group, subj, term) if student.class_group else None
        eval_stats = []
        for sg in subj_grades:
            ev = sg.evaluation
            eval_stats.append({
                "title": ev.title,
                "date": ev.date,
                "coefficient": float(ev.coefficient),
                "value": float(sg.value) if sg.value is not None else None,
                "max_grade": float(ev.scale_max),
                "min": float(ev.min_grade) if ev.min_grade is not None else None,
                "max": float(ev.max_grade) if ev.max_grade is not None else None,
                "status": sg.status,
                "comment": sg.comment,
            })
        subjects_data.append({
            "subject": subj,
            "student_average": student_avg,
            "class_average": class_avg,
            "evaluations": eval_stats,
        })

    general_avg = weighted_average(student, term)
    present_count = grades_qs.filter(status=Grade.Status.PRESENT).count()
    absent_count = grades_qs.filter(status=Grade.Status.ABSENT).count()

    # Sélecteur d'enfant pour les parents
    children = []
    if request.user.is_parent:
        children = list(request.user.parent_profile.children.select_related("user"))

    context = {
        "student": student,
        "term": term,
        "terms": terms,
        "general_average": general_avg,
        "subjects_data": subjects_data,
        "present_count": present_count,
        "absent_count": absent_count,
        "children": children,
        "selected_child_id": student.id,
    }
    return render(request, "academics/grades.html", context)


# ---------- API : sauvegarde rapide d'une note (AJAX) ----------


def _parse_grade_payload(request: HttpRequest) -> tuple[float | None, str, str]:
    """Décode la valeur / le statut envoyés en AJAX depuis le formulaire Excel-like.

    Accepte :
    - ``value`` : numérique ou vide ; les chaînes « ABS »/« DISP »/« NR »
      sont reconnues comme raccourcis de statut (cf. template).
    - ``status`` : code statut (``PRESENT``, ``ABSENT``…).
    - ``comment`` : commentaire libre.
    """
    raw_value = (request.POST.get("value") or "").strip()
    raw_status = (request.POST.get("status") or "").strip().upper()
    comment = (request.POST.get("comment") or "").strip()

    # Raccourcis clavier
    shortcuts = {
        "ABS": Grade.Status.ABSENT,
        "A": Grade.Status.ABSENT,
        "DISP": Grade.Status.DISPENSED,
        "D": Grade.Status.DISPENSED,
        "NR": Grade.Status.NOT_SUBMITTED,
        "N": Grade.Status.NOT_SUBMITTED,
        "": Grade.Status.PRESENT,
        "P": Grade.Status.PRESENT,
    }
    status = raw_status or ""
    value: float | None = None
    if raw_value.upper() in shortcuts:
        status = shortcuts[raw_value.upper()]
    elif raw_value == "":
        # Pas de valeur ni raccourci → on conserve le statut fourni
        status = status or Grade.Status.PRESENT
    else:
        # Numérique (on accepte virgule ou point)
        normalized = raw_value.replace(",", ".")
        try:
            value = float(normalized)
            if value < 0:
                value = 0.0
            status = Grade.Status.PRESENT
        except ValueError:
            # Texte libre non reconnu → pas de valeur, on conserve le statut
            value = None
            status = status or Grade.Status.PRESENT

    if status not in Grade.Status.values:
        status = Grade.Status.PRESENT

    return value, status, comment


@login_required
@require_POST
def grade_save_ajax(request: HttpRequest, grade_id: int) -> JsonResponse:
    """Endpoint AJAX : met à jour une note individuelle et renvoie les stats live."""
    if not request.user.is_teacher:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    grade = get_object_or_404(
        Grade.objects.select_related("evaluation", "student__user"),
        id=grade_id,
    )
    # Un prof ne modifie que les notes de ses propres évaluations
    teacher_profile = getattr(request.user, "teacher_profile", None)
    if (
        not request.user.is_admin
        and (teacher_profile is None or grade.evaluation.teacher_id != teacher_profile.id)
    ):
        return JsonResponse({"ok": False, "error": "not_owner"}, status=403)

    value, status, comment = _parse_grade_payload(request)
    grade.value = value if status == Grade.Status.PRESENT else None
    grade.status = status
    grade.comment = comment[:255]
    grade.save(update_fields=["value", "status", "comment", "updated_at"])

    evaluation = grade.evaluation
    return JsonResponse({
        "ok": True,
        "grade": {
            "id": grade.id,
            "value": float(grade.value) if grade.value is not None else None,
            "status": grade.status,
            "comment": grade.comment,
        },
        "stats": {
            "average": float(evaluation.average) if evaluation.average is not None else None,
            "min": float(evaluation.min_grade) if evaluation.min_grade is not None else None,
            "max": float(evaluation.max_grade) if evaluation.max_grade is not None else None,
            "present": evaluation.count_present,
            "total": evaluation.count_total,
            "attendance_rate": evaluation.attendance_rate,
        },
    })


@login_required
@require_POST
def evaluation_save_all(request: HttpRequest, evaluation_id: int) -> HttpResponse:
    """Sauvegarde « bulk » via le bouton collant (équivalent de la soumission
    de formulaire classique, conservée pour les navigateurs sans JS)."""
    if not request.user.is_teacher:
        raise PermissionDenied

    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    grades = evaluation.grades.select_related("student__user").all()

    with transaction.atomic():
        saved = 0
        for g in grades:
            # Le payload bulk envoie value_<id>/status_<id>/comment_<id>
            synthetic = type("Req", (), {})()
            synthetic.POST = {
                "value": request.POST.get(f"value_{g.id}", ""),
                "status": request.POST.get(f"status_{g.id}", ""),
                "comment": request.POST.get(f"comment_{g.id}", ""),
            }
            value, status, comment = _parse_grade_payload(synthetic)
            g.value = value if status == Grade.Status.PRESENT else None
            g.status = status
            g.comment = comment[:255]
            g.save(update_fields=["value", "status", "comment", "updated_at"])
            saved += 1

    messages.success(request, f"{saved} note(s) enregistrée(s).")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "saved": saved})
    return redirect("academics:evaluation_entry", evaluation_id=evaluation.id)