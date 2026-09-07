from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    ADMIN = "ADMIN", _("Administrateur")
    TEACHER = "TEACHER", _("Professeur")
    STUDENT = "STUDENT", _("Élève")
    PARENT = "PARENT", _("Parent")


class UserManager(BaseUserManager):
    """
    Manager basé sur l'email plutôt que le username.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("L'adresse email est obligatoire."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Le super-utilisateur doit avoir is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Le super-utilisateur doit avoir is_superuser=True."))

        return self._create_user(email, password, **extra_fields)


phone_validator = RegexValidator(
    regex=r"^\+?[\d\s().-]{6,20}$",
    message=_("Numéro de téléphone invalide."),
)


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé :
    - identification par email (username conservé pour AbstractUser mais neutralisé)
    - rôle explicite via choices
    - propriété is_<role> pratique pour les permissions/vues
    """

    username = None

    email = models.EmailField(
        _("adresse email"),
        unique=True,
        db_index=True,
    )
    first_name = models.CharField(_("prénom"), max_length=80)
    last_name = models.CharField(_("nom"), max_length=80)
    role = models.CharField(
        _("rôle"),
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    phone = models.CharField(
        _("téléphone"),
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    is_active = models.BooleanField(_("actif"), default=True)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        ordering = ("last_name", "first_name")
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.get_role_display()})" if full_name else self.email

    # ----- Helpers de rôle -----
    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_teacher(self) -> bool:
        return self.role == Role.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == Role.STUDENT

    @property
    def is_parent(self) -> bool:
        return self.role == Role.PARENT

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


# ----- Profils spécifiques par rôle (1-1 avec User) -----


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": Role.TEACHER},
    )
    employee_number = models.CharField(
        _("matricule"),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )
    subjects = models.ManyToManyField(
        "academics.Subject",
        related_name="teachers",
        blank=True,
        verbose_name=_("matières enseignées"),
    )
    hire_date = models.DateField(_("date d'embauche"), null=True, blank=True)

    class Meta:
        verbose_name = _("profil professeur")
        verbose_name_plural = _("profils professeurs")

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": Role.STUDENT},
    )
    student_number = models.CharField(
        _("numéro étudiant"),
        max_length=20,
        unique=True,
    )
    birth_date = models.DateField(_("date de naissance"), null=True, blank=True)
    class_group = models.ForeignKey(
        "academics.ClassGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("classe"),
    )
    parents = models.ManyToManyField(
        "ParentProfile",
        related_name="children",
        blank=True,
        verbose_name=_("parents"),
    )

    class Meta:
        verbose_name = _("profil élève")
        verbose_name_plural = _("profils élèves")
        ordering = ("user__last_name", "user__first_name")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_number})"


class ParentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="parent_profile",
        limit_choices_to={"role": Role.PARENT},
    )
    occupation = models.CharField(
        _("profession"),
        max_length=120,
        blank=True,
    )
    relation = models.CharField(
        _("lien de parenté"),
        max_length=20,
        choices=[
            ("MOTHER", _("Mère")),
            ("FATHER", _("Père")),
            ("GUARDIAN", _("Tuteur légal")),
            ("OTHER", _("Autre")),
        ],
        default="GUARDIAN",
    )

    class Meta:
        verbose_name = _("profil parent")
        verbose_name_plural = _("profils parents")

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        limit_choices_to={"role": Role.ADMIN},
    )
    department = models.CharField(
        _("service"),
        max_length=120,
        blank=True,
    )

    class Meta:
        verbose_name = _("profil administrateur")
        verbose_name_plural = _("profils administrateurs")

    def __str__(self):
        return self.user.get_full_name() or self.user.email