from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError, ProgrammingError


def ensure_owner_exists():
    """Refuse le démarrage de l'application sans propriétaire super-admin."""
    user_model = get_user_model()
    try:
        owner_exists = user_model.objects.filter(is_superuser=True).exists()
    except (OperationalError, ProgrammingError) as error:
        raise ImproperlyConfigured(
            "La base de données n'est pas initialisée. Appliquez les migrations "
            "avant de lancer l'application."
        ) from error

    if not owner_exists:
        raise ImproperlyConfigured(
            "Démarrage impossible : aucun compte super-administrateur/owner n'existe. "
            "Créez-en un avec 'python manage.py createsuperuser', puis relancez l'application."
        )