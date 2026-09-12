"""Modèles de l'app infirmerie — passages à l'infirmerie (accès restreint pour raisons de confidentialité)."""

from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class VisitReason(models.TextChoices):
    MALAISE = "MALAISE", _("Malaise")
    BLESSURE = "BLESSURE", _("Blessure")
    MAUX_TETE = "MAUX_TETE", _("Maux de tête")
    MAUX_VENTRE = "MAUX_VENTRE", _("Maux de ventre")
    TRAUMATISME = "TRAUMATISME", _("Traumatisme")
    AUTRE = "AUTRE", _("Autre")


class VisitOutcome(models.TextChoices):
    EN_COURS = "EN_COURS", _("Prise en charge en cours")
    RETOUR_CLASSE = "RETOUR_CLASSE", _("Retour en cours")
    RENVOYE_DOMICILE = "RENVOYE_DOMICILE", _("Renvoyé au domicile")
    HOPITAL = "HOPITAL", _("Transféré vers un hôpital")


class InfirmerieVisit(models.Model):
    """Passage d'un élève à l'infirmerie.

    Accès restreint : seuls l'infirmier/l'infirmière et l'administration
    voient le détail médical. Les professeurs ne voient qu'un indicateur
    « élève envoyé à l'infirmerie », sans motif ni soins prodigués.
    """

    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="infirmerie_visits",
        verbose_name=_("Élève"),
    )
    arrival_time = models.DateTimeField(_("Arrivée"), default=timezone.now)
    departure_time = models.DateTimeField(_("Sortie"), null=True, blank=True)
    reason = models.CharField(_("Motif"), max_length=20, choices=VisitReason.choices, default=VisitReason.AUTRE)
    reason_detail = models.CharField(_("Précision"), max_length=255, blank=True)
    care_given = models.TextField(_("Soins prodigués"), blank=True, max_length=1000)
    outcome = models.CharField(_("Suite donnée"), max_length=20, choices=VisitOutcome.choices, default=VisitOutcome.EN_COURS)
    parent_notified = models.BooleanField(_("Parents prévenus"), default=False)
    recorded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="infirmerie_visits_recorded",
        verbose_name=_("Saisi par"),
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        ordering = ("-arrival_time",)
        verbose_name = _("Passage infirmerie")
        verbose_name_plural = _("Passages infirmerie")

    def __str__(self) -> str:
        return f"{self.student} — {self.arrival_time:%d/%m/%Y %H:%M}"

    @property
    def is_ongoing(self) -> bool:
        return self.departure_time is None