from django.db import models


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", "Présent"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "En retard"
    EXCUSED = "EXCUSED", "Justifié"


class AttendanceRecord(models.Model):
    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    session = models.ForeignKey(
        "schedule.CourseSession",
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    minutes_late = models.PositiveSmallIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        "users.TeacherProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_attendances",
    )

    class Meta:
        unique_together = ("student", "session")
        ordering = ("-recorded_at",)

    def __str__(self):
        return f"{self.student} - {self.session} : {self.get_status_display()}"