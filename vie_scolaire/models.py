from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class RetardMotif(models.TextChoices):
    """Motif type d'un retard (case rapide à sélectionner à la déclaration)."""

    TRANSPORT = "TRANSPORT", _("Transport")
    FAMILIAL = "FAMILIAL", _("Raison familiale")
    MEDICAL = "MEDICAL", _("Raison médicale")
    ADMINISTRATIF = "ADMINISTRATIF", _("Démarche administrative")
    AUTRE = "AUTRE", _("Autre")


class RetardStatus(models.TextChoices):
    """État de validation d'un retard par la vie scolaire."""

    PENDING = "PENDING", _("En attente de validation")
    JUSTIFIED = "JUSTIFIED", _("Justifié")
    UNJUSTIFIED = "UNJUSTIFIED", _("Non justifié")



class RetardSource(models.TextChoices):
    MANUEL = "MANUEL", _("Déclaré manuellement")
    APPEL = "APPEL", _("Généré depuis l'appel")


class ObservationType(models.TextChoices):
    ENCOURAGEMENT = "ENCOURAGEMENT", _("Encouragement")
    AVERTISSEMENT_TRAVAIL = "AVERTISSEMENT_TRAVAIL", _("Avertissement travail")
    AVERTISSEMENT_CONDUITE = "AVERTISSEMENT_CONDUITE", _("Avertissement conduite")
    PUNITION = "PUNITION", _("Punition")
    SANCTION = "SANCTION", _("Sanction")
    NOTE = "NOTE", _("Observation / note libre")


class Observation(models.Model):
    """Une observation façon Pronote : encouragement, avertissement, punition, sanction, ou note libre."""

    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="observations",
        verbose_name=_("Élève"),
    )
    type = models.CharField(
        max_length=30,
        choices=ObservationType.choices,
        default=ObservationType.NOTE,
        verbose_name=_("Type"),
        db_index=True,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
        verbose_name=_("Matière concernée"),
    )
    title = models.CharField(_("Titre"), max_length=120, blank=True)
    description = models.TextField(_("Description"), max_length=1000, blank=True)
    author = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations_written",
        verbose_name=_("Rédigé par"),
    )
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Observation")
        verbose_name_plural = _("Observations")

    def __str__(self) -> str:
        return f"{self.get_type_display()} — {self.student} ({self.created_at:%d/%m/%Y})"

    @property
    def is_positive(self) -> bool:
        return self.type == ObservationType.ENCOURAGEMENT

class Retard(models.Model):
    """Un retard déclaré par la vie scolaire (indépendant de l'appel en cours).

    Cycle de vie :
    1. Déclaration (professeur / admin) : élève, durée, motif.
    2. Justification (élève / parent, optionnelle) : texte libre.
    3. Validation (professeur / admin) : justifié ou non justifié.
    """

    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="retards",
        verbose_name=_("Élève"),
    )
    date = models.DateField(
        default=timezone.localdate,
        verbose_name=_("Date"),
        db_index=True,
    )
    duration_minutes = models.PositiveSmallIntegerField(
        verbose_name=_("Durée (minutes)"),
    )
    motif = models.CharField(
        max_length=20,
        choices=RetardMotif.choices,
        default=RetardMotif.AUTRE,
        verbose_name=_("Motif"),
    )
    motif_detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Précision du motif"),
    )
    justification = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name=_("Justification"),
        help_text=_("Texte soumis par l'élève ou son représentant légal."),
    )
    justification_submitted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Justification soumise le"))
    status = models.CharField(
        max_length=15,
        choices=RetardStatus.choices,
        default=RetardStatus.PENDING,
        db_index=True,
        verbose_name=_("Validation"),
    )
    declared_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retards_declares",
        verbose_name=_("Déclaré par"),
    )
    validated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retards_valides",
        verbose_name=_("Validé par"),
    )
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Validé le"))
    attendance_record = models.OneToOneField(
        "attendance.AttendanceRecord",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="retard",
        verbose_name=_("Séance d'origine (appel)"),
    )
    source = models.CharField(
        max_length=10,
        choices=RetardSource.choices,
        default=RetardSource.MANUEL,
        verbose_name=_("Origine"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        ordering = ("-date", "-created_at")
        verbose_name = _("Retard")
        verbose_name_plural = _("Retards")
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student} — {self.date} ({self.duration_minutes} min)"

    @property
    def is_pending(self) -> bool:
        return self.status == RetardStatus.PENDING

    @property
    def has_justification(self) -> bool:
        return bool(self.justification)
