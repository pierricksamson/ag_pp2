"""Signaux de l'app attendance — synchronise l'appel avec le module vie scolaire.

Quand un professeur marque un élève « en retard » pendant l'appel, on crée
(ou met à jour) automatiquement le retard correspondant dans vie_scolaire,
pour éviter la double saisie. Si le statut change et n'est plus LATE, le
retard généré depuis l'appel est supprimé (les retards saisis manuellement
ne sont jamais touchés par ce signal).
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AttendanceRecord, AttendanceStatus


@receiver(post_save, sender=AttendanceRecord)
def sync_retard_from_attendance(sender, instance: AttendanceRecord, **kwargs):
    # Import tardif : évite toute dépendance circulaire au chargement des apps.
    from vie_scolaire.models import Retard, RetardSource

    existing = Retard.objects.filter(attendance_record=instance).first()

    if instance.status == AttendanceStatus.LATE:
        duration = instance.minutes_late or 1
        if existing:
            existing.duration_minutes = duration
            existing.motif_detail = instance.reason or existing.motif_detail
            existing.save(update_fields=["duration_minutes", "motif_detail"])
        else:
            Retard.objects.create(
                student=instance.student,
                date=timezone.localdate(),
                duration_minutes=duration,
                motif_detail=instance.reason or "",
                declared_by=instance.recorded_by.user if instance.recorded_by else None,
                attendance_record=instance,
                source=RetardSource.APPEL,
            )
    else:
        if existing and existing.source == RetardSource.APPEL:
            existing.delete()