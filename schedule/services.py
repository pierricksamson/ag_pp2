from django.core.exceptions import ValidationError

from .models import CourseSession


def validate_session_conflicts(session, class_group_ids=None):
    """Refuse les chevauchements de professeur, salle ou classe."""
    if not session.day or not session.start_time or not session.end_time:
        return

    overlapping = CourseSession.objects.filter(
        day=session.day,
        start_time__lt=session.end_time,
        end_time__gt=session.start_time,
    ).exclude(pk=session.pk)

    conflicts = []

    if session.teacher_id and overlapping.filter(teacher_id=session.teacher_id).exists():
        conflicts.append("Ce professeur a déjà une séance sur ce créneau.")

    if session.room_id and overlapping.filter(room_id=session.room_id).exists():
        conflicts.append("Cette salle est déjà occupée sur ce créneau.")

    class_group_ids = list(class_group_ids or [])
    if class_group_ids and overlapping.filter(class_groups__id__in=class_group_ids).exists():
        conflicts.append("Au moins une classe a déjà une séance sur ce créneau.")

    if conflicts:
        raise ValidationError({"__all__": conflicts})
