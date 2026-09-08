"""Services de calcul des moyennes — utilisées par les vues Élève / Parent."""

from __future__ import annotations

from typing import Iterable

from django.db.models import Avg, Q

from .models import Evaluation, Grade, Term


# =========================
#  Moyenne par matière (élève)
# =========================


def subject_average(student, term: Term, subject) -> float | None:
    """Moyenne pondérée par matière, sur le trimestre donné, pour un élève.

    Pondération = coefficient de l'évaluation. Les notes non présentes sont exclues.
    Renvoie None si l'élève n'a aucune note exploitable.
    """
    grades = (
        Grade.objects
        .filter(
            student=student,
            evaluation__term=term,
            evaluation__subject=subject,
            status=Grade.Status.PRESENT,
            value__isnull=False,
        )
        .select_related("evaluation")
    )
    total_weighted = 0.0
    total_coeff = 0.0
    for g in grades:
        coef = float(g.evaluation.coefficient)
        total_weighted += float(g.value) * coef
        total_coeff += coef
    if total_coeff == 0:
        return None
    return round(total_weighted / total_coeff, 2)


# =========================
#  Moyenne par matière (classe)
# =========================


def class_subject_average(class_group, subject, term: Term) -> float | None:
    """Moyenne pondérée de la classe pour une matière, sur un trimestre donné.

    On moyenne d'abord par élève (déjà pondéré par les coefficients d'épreuves),
    puis on moyenne entre élèves : c'est la convention utilisée par la plupart
    des bulletins (moyenne des moyennes élèves).
    """
    if class_group is None:
        return None

    student_ids = class_group.students.values_list("id", flat=True)
    if not student_ids:
        return None

    student_averages: list[float] = []
    for sid in student_ids:
        # On réutilise subject_average pour chaque élève (logique identique).
        from users.models import StudentProfile
        try:
            student = StudentProfile.objects.get(id=sid)
        except StudentProfile.DoesNotExist:
            continue
        avg = subject_average(student, term, subject)
        if avg is not None:
            student_averages.append(avg)

    if not student_averages:
        return None
    return round(sum(student_averages) / len(student_averages), 2)


# =========================
#  Moyenne générale pondérée (élève, trimestre)
# =========================


def weighted_average(student, term: Term) -> float | None:
    """Moyenne générale d'un élève sur un trimestre : Σ(coef_matière × moyenne_matière) / Σ(coef_matière).

    Le coefficient d'une matière est calculé comme la somme des coefficients de ses
    évaluations sur le trimestre. Une matière sans aucune note comptée est ignorée.
    """
    subjects_in_term = (
        Evaluation.objects
        .filter(term=term, class_group=student.class_group)
        .values_list("subject_id", flat=True)
        .distinct()
    )
    from academics.models import Subject  # import local pour éviter cycle

    total_weighted = 0.0
    total_coeff = 0.0
    for subj_id in subjects_in_term:
        try:
            subject = Subject.objects.get(id=subj_id)
        except Subject.DoesNotExist:
            continue
        avg = subject_average(student, term, subject)
        if avg is None:
            continue
        # Coefficient "matière" = somme des coefficients des évaluations notées.
        coeff = (
            Evaluation.objects
            .filter(term=term, class_group=student.class_group, subject=subject)
            .aggregate(total=models_sum_coefficients())
        )["total"] or 0
        coeff = float(coeff)
        if coeff <= 0:
            continue
        total_weighted += avg * coeff
        total_coeff += coeff

    if total_coeff == 0:
        return None
    return round(total_weighted / total_coeff, 2)


# Petit utilitaire Django pour SUM(coef) avec un alias propre.
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce


def models_sum_coefficients():
    return Coalesce(Sum("coefficient"), 0, output_field=DecimalField())


# =========================
#  Classement (rang dans la classe) — façon Pronote
# =========================


def class_ranking(class_group, term: Term) -> list[tuple]:
    """Classement des élèves d'une classe par moyenne générale décroissante.

    Renvoie une liste de tuples ``(student, average)`` triée par moyenne
    décroissante. Les élèves sans moyenne exploitable sont exclus.
    """
    if class_group is None:
        return []
    from users.models import StudentProfile

    students = StudentProfile.objects.filter(class_group=class_group).select_related("user")
    ranking = []
    for student in students:
        avg = weighted_average(student, term)
        if avg is not None:
            ranking.append((student, avg))
    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking


def student_rank(student, term: Term):
    """Renvoie ``(rang, effectif)`` de l'élève dans sa classe pour ce trimestre.

    Renvoie ``None`` si l'élève n'a pas de classe ou pas de moyenne exploitable.
    """
    if student.class_group is None:
        return None
    ranking = class_ranking(student.class_group, term)
    total = len(ranking)
    for index, (s, _avg) in enumerate(ranking, start=1):
        if s.id == student.id:
            return index, total
    return None