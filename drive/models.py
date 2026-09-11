"""Modèles de l'app drive — espace de stockage personnel et par classe, avec quotas par rôle."""

from __future__ import annotations

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import Role

# Quotas par défaut (en Mo) tant qu'aucune valeur n'a été enregistrée pour le rôle.
DEFAULT_QUOTA_MB = {
    Role.STUDENT: 1,
}
DEFAULT_QUOTA_MB_FALLBACK = 10


def _user_drive_path(instance, filename):
    return f"drive/users/{instance.owner_id}/{filename}"


class StorageQuota(models.Model):
    """Quota de stockage (en Mo) pour un rôle donné. Modifiable uniquement par le owner."""

    role = models.CharField(_("rôle"), max_length=20, choices=Role.choices, unique=True)
    max_mb = models.PositiveIntegerField(_("quota (Mo)"))

    class Meta:
        verbose_name = _("quota de stockage")
        verbose_name_plural = _("quotas de stockage")
        ordering = ("role",)

    def __str__(self) -> str:
        return f"{self.get_role_display()} — {self.max_mb} Mo"

    @property
    def max_bytes(self) -> int:
        return self.max_mb * 1_000_000

    @classmethod
    def default_for_role(cls, role: str) -> int:
        return DEFAULT_QUOTA_MB.get(role, DEFAULT_QUOTA_MB_FALLBACK)

    @classmethod
    def get_max_mb_for(cls, role: str) -> int:
        quota = cls.objects.filter(role=role).first()
        return quota.max_mb if quota else cls.default_for_role(role)

    @classmethod
    def get_max_bytes_for(cls, role: str) -> int:
        return cls.get_max_mb_for(role) * 1_000_000


class DriveFile(models.Model):
    """Un fichier déposé dans le Drive : personnel (class_group=None) ou partagé pour une classe."""

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="drive_files",
        verbose_name=_("propriétaire"),
    )
    class_group = models.ForeignKey(
        "academics.ClassGroup",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="drive_files",
        verbose_name=_("classe (si partagé)"),
    )
    file = models.FileField(
        _("fichier"),
        upload_to=_user_drive_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    original_name = models.CharField(_("nom original"), max_length=255)
    size_bytes = models.PositiveBigIntegerField(_("taille (octets)"), default=0)
    uploaded_at = models.DateTimeField(_("déposé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("fichier")
        verbose_name_plural = _("fichiers")
        ordering = ("-uploaded_at",)

    def __str__(self) -> str:
        return self.original_name

    @property
    def is_shared(self) -> bool:
        return self.class_group_id is not None

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / 1_000_000, 2)

    def delete(self, *args, **kwargs):
        """Supprime aussi le fichier physique du disque."""
        storage = self.file.storage
        path = self.file.name
        super().delete(*args, **kwargs)
        if path and storage.exists(path):
            storage.delete(path)