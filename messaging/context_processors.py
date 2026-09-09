from .models import Message, Conversation, ConversationKind


def messaging_notifications(request):
    """Ajoute les compteurs de notifications messagerie au contexte de chaque template."""
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Mails non lus pour l'utilisateur connecté
    unread_count = Message.objects.filter(
        to_recipients=user,
        read_at__isnull=True,
        is_draft=False,
        deleted_at__isnull=True,
    ).count()

    # Total des mails reçus (non supprimés) pour l'utilisateur connecté
    total_mail = Message.objects.filter(
        to_recipients=user,
        conversation__kind=ConversationKind.MAIL,
        deleted_at__isnull=True,
        is_draft=False,
    ).count()

    return {
        "mail_unread_count": unread_count,
        "mail_total_count": total_mail,
    }
