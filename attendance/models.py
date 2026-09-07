from django.db import models


class AttendanceStatus(models.TextChoices):
    """Statut d'une présence lors d'une séance."""

    PRESENT = "PRESENT", "Présent"
    LATE = "LATE", "En retard"
    ABSENT = "ABSENT", "Absent"
    EXCUSED = "EXCUSED", "Justifié"


class AbsenceJustification(models.Model):
    """Justification soumise par un parent (ou un élève) pour une absence/retard.

    Elle reste en statut "pending" jusqu'à ce qu'un professeur ou un admin
    la valve (ou la rejette) depuis l'interface d'appel.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvée"
        REJECTED = "REJECTED", "Rejetée"

    attendance = models.ForeignKey(
        "attendance.AttendanceRecord",
        on_delete=models.CASCADE,
        related_name="justifications",
        verbose_name=("Absence concernée"),
    )
    submitted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_justifications",
        verbose_name=("Soumis par"),
    )
    reason = models.TextField(verbose_name=("Justification"), max_length=1000)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_justifications",
        verbose_name=("Validé par"),
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=("Validé le"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("Soumis le"))

    class Meta:
        ordering = ("-created_at",)
        verbose_name = ("Justification d'absence")
        verbose_name_plural = ("Justifications d'absences")

    def __str__(self):
        return f"Justification #{self.pk} — {self.attendance}"


class AttendanceRecord(models.Model):
    """Une ligne de présence par (élève, séance de cours).

    Le professeur remplit cette grille depuis l'interface « Faire l'appel ».
    """

    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=("Élève"),
    )
    session = models.ForeignKey(
        "schedule.CourseSession",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=("Séance"),
    )
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        verbose_name=("Statut"),
        db_index=True,
    )
    minutes_late = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=("Minutes de retard"),
        help_text=("Rempli uniquement si le statut est « En retard »."),
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=("Raison (libre)"),
    )
    justified = models.BooleanField(
        default=False,
        verbose_name=("Justifié"),
        help_text=("True si une justification a été approuvée par l'enseignant ou la vie scolaire."),
    )
    justification_reason = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name=("Motif de la justification"),
    )
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name=("Enregistré le"))
    recorded_by = models.ForeignKey(
        "users.TeacherProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendances",
        verbose_name=("Saisi par"),
    )

    class Meta:
        unique_together = ("student", "session")
        ordering = ("-recorded_at",)
        verbose_name = ("Feuille de présence")
        verbose_name_plural = ("Feuilles de présence")

    def __str__(self):
        return f"{self.student} — {self.session} : {self.get_status_display()}"

    @property
    def is_late(self) -> bool:
        return self.status == AttendanceStatus.LATE

    @property
    def is_absent(self) -> bool:
        return self.status == AttendanceStatus.ABSENT

    @property
    def needs_justification(self) -> bool:
        """True si l'élève est absent/en retard et que l'absence n'est pas encore justifiée."""
        return self.status in (AttendanceStatus.ABSENT, AttendanceStatus.LATE) and not self.justified