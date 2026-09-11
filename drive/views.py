"""Vues de l'app drive — espace personnel et dossiers de classe, avec quotas par rôle."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from academics.models import ClassGroup
from users.models import Role

from .models import DriveFile, StorageQuota

MAX_UPLOAD_NAME_LENGTH = 255


def _usage_bytes(user) -> int:
    return DriveFile.objects.filter(owner=user).aggregate(total=Sum("size_bytes"))["total"] or 0


def _quota_bytes(user) -> int:
    return StorageQuota.get_max_bytes_for(user.role)


def _user_classes(user):
    """Classes dont l'utilisateur peut voir le Drive partagé."""
    if user.is_admin:
        return ClassGroup.objects.select_related("level", "academic_year").order_by("level__order", "name")
    if user.is_teacher:
        profile = getattr(user, "teacher_profile", None)
        if profile:
            return profile.class_groups.select_related("level", "academic_year").order_by("name")
        return ClassGroup.objects.none()
    if user.is_student:
        profile = getattr(user, "student_profile", None)
        if profile and profile.class_group_id:
            return ClassGroup.objects.filter(id=profile.class_group_id)
        return ClassGroup.objects.none()
    return ClassGroup.objects.none()


def _can_manage_class_drive(user, class_group: ClassGroup) -> bool:
    """Peut supprimer n'importe quel fichier du dossier de classe (modération)."""
    if user.is_admin:
        return True
    if user.is_teacher:
        profile = getattr(user, "teacher_profile", None)
        return bool(profile and profile.class_groups.filter(id=class_group.id).exists())
    return False


def _handle_upload(request: HttpRequest, class_group: ClassGroup | None) -> None:
    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, "Merci de choisir un fichier.")
        return

    if not uploaded.name.lower().endswith(".pdf"):
        messages.error(request, "Seuls les fichiers PDF sont acceptés pour le moment.")
        return

    usage = _usage_bytes(request.user)
    quota = _quota_bytes(request.user)
    if usage + uploaded.size > quota:
        remaining_mb = max(0, quota - usage) / 1_000_000
        messages.error(
            request,
            f"Espace insuffisant : il vous reste {remaining_mb:.2f} Mo, "
            f"ce fichier fait {uploaded.size / 1_000_000:.2f} Mo.",
        )
        return

    DriveFile.objects.create(
        owner=request.user,
        class_group=class_group,
        file=uploaded,
        original_name=uploaded.name[:MAX_UPLOAD_NAME_LENGTH],
        size_bytes=uploaded.size,
    )
    messages.success(request, "Fichier envoyé.")


@login_required
def personal_drive(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        _handle_upload(request, class_group=None)
        return redirect("drive:personal")

    files = DriveFile.objects.filter(owner=request.user, class_group__isnull=True).order_by("-uploaded_at")
    usage = _usage_bytes(request.user)
    quota = _quota_bytes(request.user)

    context = {
        "files": files,
        "usage_mb": round(usage / 1_000_000, 2),
        "quota_mb": round(quota / 1_000_000, 2),
        "usage_pct": min(100, round(100 * usage / quota, 1)) if quota else 0,
        "classes": _user_classes(request.user),
    }
    return render(request, "drive/personal.html", context)


@login_required
def class_drive(request: HttpRequest, class_group_id: int) -> HttpResponse:
    class_group = get_object_or_404(ClassGroup, id=class_group_id)
    if class_group not in _user_classes(request.user):
        raise PermissionDenied

    if request.method == "POST":
        _handle_upload(request, class_group=class_group)
        return redirect("drive:class_drive", class_group_id=class_group.id)

    files = DriveFile.objects.filter(class_group=class_group).select_related("owner").order_by("-uploaded_at")
    usage = _usage_bytes(request.user)
    quota = _quota_bytes(request.user)

    context = {
        "class_group": class_group,
        "files": files,
        "usage_mb": round(usage / 1_000_000, 2),
        "quota_mb": round(quota / 1_000_000, 2),
        "usage_pct": min(100, round(100 * usage / quota, 1)) if quota else 0,
        "classes": _user_classes(request.user),
        "can_moderate": _can_manage_class_drive(request.user, class_group),
    }
    return render(request, "drive/class_drive.html", context)


@login_required
@require_POST
def delete_file(request: HttpRequest, file_id: int) -> HttpResponse:
    drive_file = get_object_or_404(DriveFile, id=file_id)

    is_owner = drive_file.owner_id == request.user.id
    can_moderate = drive_file.is_shared and _can_manage_class_drive(request.user, drive_file.class_group)
    if not (is_owner or can_moderate):
        raise PermissionDenied

    if drive_file.is_shared:
        redirect_response = redirect("drive:class_drive", class_group_id=drive_file.class_group_id)
    else:
        redirect_response = redirect("drive:personal")

    drive_file.delete()
    messages.success(request, "Fichier supprimé.")
    return redirect_response


# ---------- Owner : gestion des quotas ----------


@login_required
def quota_settings(request: HttpRequest) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        for role_value, _label in Role.choices:
            raw = request.POST.get(f"quota_{role_value}")
            if raw is None or raw == "":
                continue
            try:
                max_mb = max(1, int(raw))
            except ValueError:
                continue
            StorageQuota.objects.update_or_create(role=role_value, defaults={"max_mb": max_mb})
        messages.success(request, "Quotas mis à jour.")
        return redirect("drive:quota_settings")

    existing = {q.role: q.max_mb for q in StorageQuota.objects.all()}
    rows = [
        {
            "role": role_value,
            "label": label,
            "max_mb": existing.get(role_value, StorageQuota.default_for_role(role_value)),
            "is_default": role_value not in existing,
        }
        for role_value, label in Role.choices
    ]

    return render(request, "drive/quotas.html", {"rows": rows})