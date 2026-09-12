from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import AccountCreationForm
from .models import ParentProfile, Role, StudentProfile, TeacherProfile, User


def _can_manage_accounts(user) -> bool:
    return user.is_superuser or user.has_perm("users.can_create_accounts")


# ---------- Authentification par email ----------


class LoginView(DjangoLoginView):
    """
    Vue de connexion basée sur l'email.
    AuthenticationForm attend un champ `username` ; on le remplace par `email`
    et on adapte l'auth dans la méthode `form_valid`.
    """

    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("users:role_redirect")
        return super().get(request)

    def form_valid(self, form):
        # AuthenticationForm a validé un couple (username, password).
        # On réauthentifie en utilisant le champ email du formulaire.
        email = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, email=email, password=password)
        if user is None:
            form.add_error(None, "Email ou mot de passe incorrect.")
            return self.form_invalid(form)

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        # Si un `next` sûr est présent, on le respecte.
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse("users:role_redirect")


class LogoutView(DjangoLoginView):
    """Déconnexion : GET ou POST → on supprime la session puis on redirige."""

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Vous avez été déconnecté.")
        return redirect("users:login")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


# ---------- Redirection par rôle ----------


def role_redirect(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("users:login")

    user = request.user
    if user.is_admin:
        return redirect("users:dashboard_admin")
    if user.is_teacher:
        return redirect("users:dashboard_teacher")
    if user.is_student:
        return redirect("users:dashboard_student")
    if user.is_parent:
        return redirect("users:dashboard_parent")
    if user.is_nurse:
        return redirect("infirmerie:dashboard")
    # Fallback prudent
    return redirect("users:login")


# ---------- Dashboards ----------


def _dashboard_access(request: HttpRequest, expected_role: str) -> HttpResponse | None:
    """
    Renvoie la réponse de refus si l'utilisateur n'a pas le rôle attendu,
    ou None si tout est ok. Les vues appellent cette vérification au début.
    """
    user = request.user
    if not user.is_authenticated:
        return redirect("users:login")
    if not getattr(user, f"is_{expected_role}", False):
        messages.error(
            request,
            "Accès refusé : cette page est réservée à un autre rôle.",
        )
        return redirect("users:role_redirect")
    return None


@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    guard = _dashboard_access(request, "admin")
    if guard is not None:
        return guard

    from django.urls import reverse as _reverse

    admin_link = _reverse("admin:index")
    return render(
        request,
        "users/dashboard_admin.html",
        {
            "admin_url": admin_link,
            "stats": {
                "eleves": __import__("users.models", fromlist=["StudentProfile"]).StudentProfile.objects.count(),
                "profs": __import__("users.models", fromlist=["TeacherProfile"]).TeacherProfile.objects.count(),
                "parents": __import__("users.models", fromlist=["ParentProfile"]).ParentProfile.objects.count(),
            },
        },
    )


@login_required
def teacher_dashboard(request: HttpRequest) -> HttpResponse:
    guard = _dashboard_access(request, "teacher")
    if guard is not None:
        return guard

    profile = getattr(request.user, "teacher_profile", None)
    subjects = profile.subjects.all() if profile else []
    return render(
        request,
        "users/dashboard_teacher.html",
        {"profile": profile, "subjects": subjects},
    )


@login_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    guard = _dashboard_access(request, "student")
    if guard is not None:
        return guard

    profile = getattr(request.user, "student_profile", None)
    parents = profile.parents.select_related("user").all() if profile else []
    return render(
        request,
        "users/dashboard_student.html",
        {"profile": profile, "parents": parents},
    )


@login_required
def parent_dashboard(request: HttpRequest) -> HttpResponse:
    guard = _dashboard_access(request, "parent")
    if guard is not None:
        return guard

    profile = getattr(request.user, "parent_profile", None)
    children = profile.children.select_related("user", "class_group").all() if profile else []
    return render(
        request,
        "users/dashboard_parent.html",
        {"profile": profile, "children": children},
    )


@login_required
@require_http_methods(["GET", "POST"])
def account_management(request: HttpRequest) -> HttpResponse:
    """Création de comptes et délégation du droit de création."""
    if not _can_manage_accounts(request.user):
        messages.error(request, "Vous n'êtes pas autorisé à créer des comptes.")
        return redirect("users:role_redirect")

    account_permission = Permission.objects.get(
        content_type__app_label="users",
        codename="can_create_accounts",
    )
    users = User.objects.exclude(pk=request.user.pk).prefetch_related("user_permissions", "groups")
    groups = Group.objects.prefetch_related("permissions").order_by("name")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_account":
            form = AccountCreationForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    user = form.save()
                    if user.role == Role.STUDENT:
                        StudentProfile.objects.create(user=user, student_number=f"ELEVE-{user.pk:05d}", class_group=form.cleaned_data.get("class_group"))
                    elif user.role == Role.PARENT:
                        profile = ParentProfile.objects.create(user=user)
                        profile.children.set(form.cleaned_data.get("children", []))
                    elif user.role == Role.TEACHER:
                        profile = TeacherProfile.objects.create(user=user)
                        profile.class_groups.set(form.cleaned_data.get("teacher_classes", []))
                messages.success(
                    request,
                    f"Compte créé pour {user.get_full_name()}. Identifiant : {form.generated_email}. "
                    f"Mot de passe temporaire : {form.generated_password}",
                )
                return redirect("users:account_management")
        elif action == "save_permissions" and request.user.is_superuser:
            allowed_user_ids = {int(value) for value in request.POST.getlist("account_users") if value.isdigit()}
            allowed_group_ids = {int(value) for value in request.POST.getlist("account_groups") if value.isdigit()}
            for user in User.objects.exclude(pk=request.user.pk):
                if user.pk in allowed_user_ids:
                    user.user_permissions.add(account_permission)
                else:
                    user.user_permissions.remove(account_permission)
            for group in Group.objects.all():
                if group.pk in allowed_group_ids:
                    group.permissions.add(account_permission)
                else:
                    group.permissions.remove(account_permission)
            messages.success(request, "Les autorisations de création ont été mises à jour.")
            return redirect("users:account_management")
        elif action == "create_group" and request.user.is_superuser:
            group_name = request.POST.get("group_name", "").strip()
            if not group_name:
                messages.error(request, "Le nom du groupe est obligatoire.")
            elif Group.objects.filter(name__iexact=group_name).exists():
                messages.error(request, "Ce groupe existe déjà.")
            else:
                Group.objects.create(name=group_name)
                messages.success(request, f"Le groupe « {group_name} » a été créé.")
            return redirect("users:account_management")
        else:
            form = AccountCreationForm()
    else:
        form = AccountCreationForm()

    return render(
        request,
        "users/account_management.html",
        {
            "form": form,
            "users": users,
            "groups": groups,
            "account_permission": account_permission,
            "can_edit_permissions": request.user.is_superuser,
        },
    )