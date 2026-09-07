"""Vues de l'app schedule.

La vue ``weekly_schedule`` adapte la grille hebdomadaire au rôle de
l'utilisateur :

- **Élève** : voit l'emploi du temps de sa classe.
- **Professeur** : voit ses propres séances.
- **Admin** : peut filtrer par classe, professeur ou salle.

La grille générée est envoyée à ``schedule/weekly.html`` qui pose les blocs
par-dessus avec Tailwind (positionnement CSS Grid ``grid-row-start``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from academics.models import ClassGroup
from users.models import Role, StudentProfile, TeacherProfile

from .models import CourseSession, Room


# ---------- Constantes de la grille ----------


@dataclass(frozen=True)
class GridConfig:
    """Configuration de la grille hebdomadaire."""

    days: tuple[tuple[str, str], ...] = (
        ("MON", "Lundi"),
        ("TUE", "Mardi"),
        ("WED", "Mercredi"),
        ("THU", "Jeudi"),
        ("FRI", "Vendredi"),
        ("SAT", "Samedi"),
    )
    grid_start: time = time(8, 0)
    grid_end: time = time(19, 0)
    # 1 unité de grille = 30 minutes (utilisé pour ``grid-row-start/end``).
    slot_minutes: int = 30

    @property
    def total_rows(self) -> int:
        delta = (
            self.grid_end.hour * 60 + self.grid_end.minute
        ) - (
            self.grid_start.hour * 60 + self.grid_start.minute
        )
        return max(delta // self.slot_minutes, 1)


GRID = GridConfig()


def _time_to_row(t: time) -> int:
    """Convertit une heure en numéro de ligne de la grille (1-indexé)."""
    minutes = (t.hour - GRID.grid_start.hour) * 60 + (t.minute - GRID.grid_start.minute)
    return max(minutes // GRID.slot_minutes, 0) + 2  # +2 = header + base 1


def _duration_rows(start: time, end: time) -> int:
    delta_min = (end.hour - start.hour) * 60 + (end.minute - start.minute)
    if delta_min <= 0:
        return 1
    return max(delta_min // GRID.slot_minutes, 1)


def _hour_marks() -> list[dict]:
    """Liste des marqueurs horaires affichés dans la colonne de gauche."""
    marks = []
    cur = time(GRID.grid_start.hour, 0)
    end = GRID.grid_end
    while cur <= end:
        marks.append({"label": cur.strftime("%H:%M"), "hour": cur.hour})
        cur = time((cur.hour + 1) % 24, cur.minute)
    return marks


# ---------- Vue principale ----------


@login_required
def weekly_schedule(request: HttpRequest) -> HttpResponse:
    """Emploi du temps hebdomadaire, adapté au rôle."""

    user = request.user
    qs = CourseSession.objects.select_related(
        "subject", "teacher__user", "room"
    ).prefetch_related("class_groups")

    role = "guest"
    context_filters: dict = {}
    sessions = qs.none()

    if user.is_admin:
        role = "admin"
        # Filtres admin
        class_id = request.GET.get("class")
        teacher_id = request.GET.get("teacher")
        room_id = request.GET.get("room")
        filters = Q()
        if class_id:
            filters &= Q(class_groups__id=class_id)
        if teacher_id:
            filters &= Q(teacher_id=teacher_id)
        if room_id:
            filters &= Q(room_id=room_id)
        sessions = qs.filter(filters).distinct() if filters else qs.all()
        context_filters = {
            "class_id": class_id or "",
            "teacher_id": teacher_id or "",
            "room_id": room_id or "",
            "class_groups": ClassGroup.objects.select_related("level", "academic_year").order_by("level__order", "name"),
            "teachers": TeacherProfile.objects.select_related("user").order_by("user__last_name", "user__first_name"),
            "rooms": Room.objects.all().order_by("name"),
        }
    elif user.is_teacher:
        role = "teacher"
        profile = getattr(user, "teacher_profile", None)
        if profile is None:
            raise PermissionDenied("Aucun profil professeur associé à ce compte.")
        sessions = qs.filter(teacher=profile)
    elif user.is_student:
        role = "student"
        profile: StudentProfile | None = getattr(user, "student_profile", None)
        if profile is None or profile.class_group is None:
            raise PermissionDenied("Aucun profil élève ou classe associée.")
        sessions = qs.filter(class_groups=profile.class_group)
    elif user.is_parent:
        # Parent : redirige vers la sélection de l'enfant via les notes
        from django.shortcuts import redirect
        return redirect("academics:grades")
    else:
        raise PermissionDenied

    # Prépare les sessions pour la grille : on calcule ``row_start``/``row_end``
    blocks = []
    for s in sessions.order_by("day", "start_time"):
        blocks.append({
            "session": s,
            "row_start": _time_to_row(s.start_time),
            "row_span": _duration_rows(s.start_time, s.end_time),
            "color": s.color_class,
            "label": s.display_label,
            "classes": ", ".join(str(g) for g in s.class_groups.all()),
        })

    context = {
        "role": role,
        "blocks": blocks,
        "days": [{"code": code, "label": label} for code, label in GRID.days],
        "hour_marks": _hour_marks(),
        "grid_start_row": 2,  # 1 = header, on place la 1ʳᵉ ligne horaire à 2
        "total_rows": GRID.total_rows + 1,
        "filters": context_filters,
    }
    return render(request, "schedule/weekly.html", context)