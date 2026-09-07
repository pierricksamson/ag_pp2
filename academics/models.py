"""Modèles de l'app academics — gestion des périodes, classes, matières, évaluations et notes."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.utils.translation import gettext_lazy as _


# =========================
#  Référentiels académiques
# =========================


class AcademicYear(models.Model):
    """Année scolaire (ex : 2025-2026)."""

    label = models.CharField(_("libellé"), max_length=20, unique=True)
    start_date = models.DateField(_("date de début"))
    end_date = models.DateField(_("date de fin"))
    is_current = models.BooleanField(_("active"), default=False)

    class Meta:
        ordering = ("-start_date",)
        verbose_name = _("année scolaire")
        verbose_name_plural = _("années scolaires")

    def __str__(self) -> str:
        return self.label


class Level(models.Model):
    """Niveau scolaire (ex : 6ème, 5ème)."""

    name = models.CharField(_("nom"), max_length=60, unique=True)
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)

    class Meta:
        ordering = ("order",)
        verbose_name = _("niveau")
        verbose_name_plural = _("niveaux")

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    """Matière enseignée (rattachée à un niveau)."""

    code = models.CharField(_("code"), max_length=10, unique=True)
    name = models.CharField(_("nom"), max_length=120)
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name="subjects",
        verbose_name=_("niveau"),
    )

    class Meta:
        ordering = ("name",)
        verbose_name = _("matière")
        verbose_name_plural = _("matières")

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ClassGroup(models.Model):
    """Classe d'élèves (ex : 6ème A, 3ème B)."""

    name = models.CharField(_("nom"), max_length=40)
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name="class_groups",
        verbose_name=_("niveau"),
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="class_groups",
        verbose_name=_("année scolaire"),
    )

    class Meta:
        ordering = ("level", "name")
        verbose_name = _("classe")
        verbose_name_plural = _("classes")
        unique_together = (("name", "level", "academic_year"),)

    def __str__(self) -> str:
        return f"{self.level.name} {self.name}"


class Term(models.Model):
    """Période / trimestre sur une année scolaire."""

    name = models.CharField(_("nom"), max_length=60)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
        verbose_name=_("année scolaire"),
    )
    start_date = models.DateField(_("date de début"))
    end_date = models.DateField(_("date de fin"))
    is_current = models.BooleanField(_("active"), default=False)

    class Meta:
        ordering = ("academic_year", "start_date")
        verbose_name = _("trimestre")
        verbose_name_plural = _("trimestres")
        unique_together = (("name", "academic_year"),)

    def __str__(self) -> str:
        return f"{self.name} — {self.academic_year.label}"


# =========================
#  Évaluations et notes
# =========================


class Evaluation(models.Model):
    """Une épreuve notée (contrôle, DS, interro…) pour une classe + matière + professeur + trimestre."""

    title = models.CharField(_("titre"), max_length=120)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="evaluations",
        verbose_name=_("matière"),
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("classe"),
    )
    teacher = models.ForeignKey(
        "users.TeacherProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations",
        verbose_name=_("professeur"),
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("trimestre"),
    )
    date = models.DateField(_("date de l'épreuve"))
    coefficient = models.DecimalField(
        _("coefficient"),
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    scale_max = models.DecimalField(
        _("note maximale"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField(_("créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifiée le"), auto_now=True)

    class Meta:
        verbose_name = _("évaluation")
        verbose_name_plural = _("évaluations")
        ordering = ("-date", "-id")

    def __str__(self) -> str:
        return f"{self.title} — {self.subject.code} ({self.class_group})"

    # ----- Statistiques en direct (ignoré les non notés) -----

    def _present_grades(self):
        return self.grades.filter(
            status=Grade.Status.PRESENT, value__isnull=False
        )

    @property
    def average(self):
        """Moyenne de la classe (notes présentes uniquement)."""
        result = self._present_grades().aggregate(avg=Avg("value"))
        return result["avg"]

    @property
    def min_grade(self):
        result = self._present_grades().aggregate(min=models.Min("value"))
        return result["min"]

    @property
    def max_grade(self):
        result = self._present_grades().aggregate(max=models.Max("value"))
        return result["max"]

    @property
    def count_total(self) -> int:
        return self.grades.count()

    @property
    def count_present(self) -> int:
        return self._present_grades().count()

    @property
    def attendance_rate(self) -> float:
        """Taux de présence en % sur la classe."""
        total = self.count_total
        if not total:
            return 0.0
        return round(100 * self.count_present / total, 1)


class Grade(models.Model):
    """Note obtenue par un élève à une évaluation."""

    class Status(models.TextChoices):
        PRESENT = "PRESENT", _("Présent")
        ABSENT = "ABSENT", _("Absent")
        DISPENSED = "DISPENSED", _("Dispensé")
        NOT_SUBMITTED = "NOT_SUBMITTED", _("Non rendu")

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("évaluation"),
    )
    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("élève"),
    )
    value = models.DecimalField(
        _("note"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Note sur la valeur maximale de l'évaluation."),
    )
    status = models.CharField(
        _("statut"),
        max_length=15,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    comment = models.CharField(_("appréciation / commentaire"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifiée le"), auto_now=True)

    class Meta:
        ordering = ("student__user__last_name", "student__user__first_name")
        verbose_name = _("note")
        verbose_name_plural = _("notes")
        unique_together = (("evaluation", "student"),)

    def __str__(self) -> str:
        return f"{self.student} — {self.evaluation} → {self.value or self.status}"

    # ----- Helpers -----

    @property
    def is_counted_in_average(self) -> bool:
        """Une note compte dans la moyenne uniquement si elle est présente ET a une valeur."""
        return self.status == self.Status.PRESENT and self.value is not None

    @property
    def normalized_value(self) -> float | None:
        """Valeur ramenée sur 20 (utile pour les moyennes pondérées inter-matières)."""
        if not self.is_counted_in_average:
            return None
        try:
            v = float(self.value)
            m = float(self.evaluation.scale_max)
            if m <= 0:
                return None
            return v * 20.0 / m
        except (TypeError, ValueError):
            return None