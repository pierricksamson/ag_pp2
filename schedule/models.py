"""Modèles de l'app schedule — salles et séances de cours hebdomadaires.

Le modèle est volontairement flexible :
- ``CourseSession`` accepte une liste de classes (TD regroupés, amphis partagés…).
- Les horaires sont stockés directement en ``TimeField`` (start/end) pour couvrir
  aussi bien les séances courtes du primaire/collège (45-55 min) que les amphis
  du supérieur (2 à 4 h).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# =========================
#  Référentiels
# =========================


class Room(models.Model):
    """Salle ou espace physique où se déroule un cours (classe, labo, gymnase…).

    Modèle volontairement minimal pour rester compatible aussi bien avec une
    petite école primaire qu'avec une université (amphis, laboratoires, etc.).
    """

    name = models.CharField(_("nom"), max_length=60, unique=True)
    capacity = models.PositiveSmallIntegerField(_("capacité"), default=30)
    location = models.CharField(
        _("bâtiment / étage"),
        max_length=120,
        blank=True,
        help_text=_("Indication libre, ex : « Bâtiment A, 1er étage »."),
    )

    class Meta:
        ordering = ("name",)
        verbose_name = _("salle")
        verbose_name_plural = _("salles")

    def __str__(self) -> str:
        return self.name


# =========================
#  Séances de cours
# =========================


class CourseSession(models.Model):
    """Séance planifiée dans l'emploi du temps hebdomadaire.

    Une séance peut concerner **plusieurs classes** (CMI/TD regroupés, amphi
    partagé entre plusieurs L1, etc.). À l'inverse, une séance n'a qu'un
    enseignant, une matière et une salle.
    """

    class Day(models.TextChoices):
        MONDAY = "MON", _("Lundi")
        TUESDAY = "TUE", _("Mardi")
        WEDNESDAY = "WED", _("Mercredi")
        THURSDAY = "THU", _("Jeudi")
        FRIDAY = "FRI", _("Vendredi")
        SATURDAY = "SAT", _("Samedi")

    title = models.CharField(
        _("intitulé"),
        max_length=120,
        blank=True,
        help_text=_("Optionnel : ex « CM1+CM2 », « Amphi L1 Info ». Laisser vide pour utiliser la matière."),
    )

    class_groups = models.ManyToManyField(
        "academics.ClassGroup",
        related_name="sessions",
        verbose_name=_("classes"),
        help_text=_("Une ou plusieurs classes (CMI, TD regroupés, amphi partagé…)."),
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("matière"),
    )
    teacher = models.ForeignKey(
        "users.TeacherProfile",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("professeur"),
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        verbose_name=_("salle"),
    )

    day = models.CharField(
        _("jour"),
        max_length=3,
        choices=Day.choices,
    )
    start_time = models.TimeField(_("heure de début"))
    end_time = models.TimeField(_("heure de fin"))

    color = models.CharField(
        _("couleur"),
        max_length=20,
        blank=True,
        help_text=_("Classe Tailwind « bg-* » optionnelle pour la carte."),
    )

    class Meta:
        ordering = ("day", "start_time", "subject__name")
        verbose_name = _("séance")
        verbose_name_plural = _("séances")
        indexes = [
            models.Index(fields=["day", "start_time"]),
        ]

    def __str__(self) -> str:
        label = self.title or str(self.subject)
        groups = ", ".join(str(g) for g in self.class_groups.all()) or "—"
        return f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M} · {label} ({groups})"

    # ----- Helpers -----

    @property
    def duration_minutes(self) -> int:
        """Durée de la séance en minutes (supporte les amphis > 1 h)."""
        start = self.start_time
        end = self.end_time
        delta = (
            end.hour * 60 + end.minute
        ) - (
            start.hour * 60 + start.minute
        )
        return max(delta, 0)

    @property
    def display_label(self) -> str:
        return self.title or self.subject.name

    @property
    def color_class(self) -> str:
        """Renvoie une classe Tailwind de fond basée sur la couleur stockée
        ou déduite du code matière."""
        if self.color:
            return self.color
        palette = [
            "bg-brand-100 text-brand-700 border-brand-200",
            "bg-emerald-100 text-emerald-700 border-emerald-200",
            "bg-amber-100 text-amber-700 border-amber-200",
            "bg-rose-100 text-rose-700 border-rose-200",
            "bg-violet-100 text-violet-700 border-violet-200",
            "bg-sky-100 text-sky-700 border-sky-200",
            "bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200",
            "bg-teal-100 text-teal-700 border-teal-200",
        ]
        seed = (self.subject.code or self.subject.name or "").strip()
        if not seed:
            return palette[0]
        return palette[sum(ord(c) for c in seed) % len(palette)]