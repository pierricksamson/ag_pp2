from __future__ import annotations

from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from users.models import User

from .models import Conversation, ConversationKind, Message

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff_member)


def _rows_for(user: User, kind: str) -> list[dict]:
    conversations = (
        Conversation.objects.filter(participants=user, kind=kind)
        .prefetch_related("participants", "messages")
        .distinct()
    )
    rows = []
    for c in conversations:
        last = c.messages.filter(deleted_at__isnull=True).last()
        unread = c.messages.filter(deleted_at__isnull=True).exclude(sender=user).filter(read_at__isnull=True).count()
        others = c.participants.exclude(id=user.id)
        rows.append({
            "conversation": c,
            "others": others,
            "last_message": last,
            "unread": unread,
        })
    rows.sort(key=lambda r: r["last_message"].sent_at if r["last_message"] else r["conversation"].created_at, reverse=True)
    return rows


def _mail_conversations(user: User) -> list[Conversation]:
    conversations = (
        Conversation.objects.filter(kind=ConversationKind.MAIL)
        .prefetch_related("participants", "messages")
        .distinct()
    )
    rows = []
    for c in conversations:
        last = c.messages.filter(deleted_at__isnull=True).last()
        unread = c.messages.filter(deleted_at__isnull=True).exclude(sender=user).filter(read_at__isnull=True).count()
        others = c.participants.exclude(id=user.id)
        rows.append({
            "conversation": c,
            "others": others,
            "last_message": last,
            "unread": unread,
        })
    rows.sort(key=lambda r: r["last_message"].sent_at if r["last_message"] else r["conversation"].created_at, reverse=True)
    return rows


@login_required
def inbox(request: HttpRequest) -> HttpResponse:
    rows = _mail_conversations(request.user)
    unread_count = Message.objects.filter(
        to_recipients=request.user,
        read_at__isnull=True,
        is_draft=False,
        deleted_at__isnull=True,
    ).count()
    draft_count = Message.objects.filter(
        is_draft=True,
        deleted_at__isnull=True,
    ).count()
    return render(request, "messaging/inbox.html", {
        "rows": rows,
        "unread_count": unread_count,
        "draft_count": draft_count,
    })


@login_required
def sent(request: HttpRequest) -> HttpResponse:
    """Afficher les messages envoyés par l'utilisateur."""
    sent_messages = (
        Message.objects.filter(sender=request.user, is_draft=False, deleted_at__isnull=True)
        .select_related("conversation")
        .order_by("-sent_at")
    )
    # Also get draft count for sidebar
    draft_count = Message.objects.filter(
        is_draft=True,
        deleted_at__isnull=True,
    ).count()
    return render(request, "messaging/sent.html", {
        "sent_messages": sent_messages,
        "draft_count": draft_count,
    })


@login_required
def drafts(request: HttpRequest) -> HttpResponse:
    """Afficher les messages brouillons (non envoyés)."""
    drafts = (
        Message.objects.filter(is_draft=True, deleted_at__isnull=True)
        .select_related("sender", "conversation")
        .order_by("-sent_at")
    )
    draft_count = drafts.count()
    return render(request, "messaging/drafts.html", {
        "drafts": drafts,
        "draft_count": draft_count,
    })


@login_required
def trash(request: HttpRequest) -> HttpResponse:
    """Afficher les messages supprimés (corbeille)."""
    deleted = Message.objects.filter(deleted_at__isnull=False).order_by("-sent_at")
    draft_count = Message.objects.filter(
        is_draft=True,
        deleted_at__isnull=True,
    ).count()
    return render(request, "messaging/trash.html", {
        "trash": deleted,
        "draft_count": draft_count,
    })


@login_required
def new_conversation(request: HttpRequest, message_id: int = None) -> HttpResponse:
    recipients_qs = User.objects.order_by("role", "last_name", "first_name")
    initial_recipients = []
    draft_body = ""
    draft_subject = ""
    is_reply = False
    is_forward = False
    
    if message_id:
        original_message = get_object_or_404(Message, id=message_id)
        if original_message.in_reply_to:
            parent = original_message.in_reply_to
        else:
            parent = original_message
        
        conversation = parent.conversation
        is_reply = False
        is_forward = False
        
        # Check if the user is a participant in the original conversation
        if conversation.participants.filter(id=request.user.id).exists():
            # Reply: notify participants except sender
            participants = conversation.participants.exclude(id=original_message.sender_id)
            initial_recipients = list(participants.values_list("id", flat=True))
            draft_body = f"Re: {original_message.subject or ''}\n\n{original_message.body}\n\n"
            draft_subject = f"Re: {original_message.subject or ''}"
            is_reply = True
        else:
            # Forward: notify no one by default
            draft_body = f"Transfert: {original_message.subject or ''}\n\n{original_message.body}\n\n"
            draft_subject = f"Fwd: {original_message.subject or ''}"
            is_forward = True
        
        if request.method == "POST":
            to_ids = request.POST.getlist("to")
            cc_ids = request.POST.getlist("cc")
            bcc_ids = request.POST.getlist("bcc")
            subject = (request.POST.get("subject") or conversation.subject or "").strip()
            body = (request.POST.get("body") or "").strip()
            save_as_draft = request.POST.get("save_as_draft")

            if not to_ids or not body:
                django_messages.error(request, "Destinataire(s) et message sont obligatoires.")
            else:
                to_recipients = User.objects.filter(id__in=to_ids)
                cc_recipients = User.objects.filter(id__in=cc_ids)
                bcc_recipients = User.objects.filter(id__in=bcc_ids)
                new_conversation_obj = Conversation.objects.create(kind=ConversationKind.MAIL, subject=subject[:120])
                new_conversation_obj.participants.add(request.user, *to_recipients, *cc_recipients, *bcc_recipients)
                message = Message.objects.create(
                    conversation=new_conversation_obj,
                    sender=request.user,
                    subject=subject[:120],
                    body=body[:5000],
                    is_draft=False,
                )
                message.to_recipients.set(to_recipients)
                message.cc_recipients.set(cc_recipients)
                message.bcc_recipients.set(bcc_recipients)
                django_messages.success(request, "Message envoyé.")
                return redirect("messaging:conversation_detail", conversation_id=new_conversation_obj.id)

    else:
        recipients_qs = User.objects.order_by("role", "last_name", "first_name")

        if request.method == "POST":
            to_ids = request.POST.getlist("to")
            cc_ids = request.POST.getlist("cc")
            bcc_ids = request.POST.getlist("bcc")
            subject = (request.POST.get("subject") or "").strip()
            body = (request.POST.get("body") or "").strip()
            save_as_draft = request.POST.get("save_as_draft")

            if not to_ids or not body:
                django_messages.error(request, "Destinataire(s) et message sont obligatoires.")
            else:
                to_recipients = User.objects.filter(id__in=to_ids)
                cc_recipients = User.objects.filter(id__in=cc_ids)
                bcc_recipients = User.objects.filter(id__in=bcc_ids)
                conversation = Conversation.objects.create(kind=ConversationKind.MAIL, subject=subject[:120])
                conversation.participants.add(request.user, *to_recipients, *cc_recipients, *bcc_recipients)
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    subject=subject[:120],
                    body=body[:5000],
                    is_draft=bool(save_as_draft),
                )
                message.to_recipients.set(to_recipients)
                message.cc_recipients.set(cc_recipients)
                message.bcc_recipients.set(bcc_recipients)
                if save_as_draft:
                    django_messages.success(request, "Brouillon enregistré.")
                    return redirect("messaging:drafts")
                django_messages.success(request, "Message envoyé.")
                return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    initial_users = User.objects.filter(id__in=initial_recipients) if initial_recipients else []
    return render(request, "messaging/new_conversation.html", {
        "recipients": recipients_qs,
        "initial_recipients": initial_users,
        "draft_body": draft_body,
        "draft_subject": draft_subject,
        "is_reply": is_reply,
        "is_forward": is_forward,
    })


@login_required
def reply(request: HttpRequest, message_id: int) -> HttpResponse:
    """Répondre à un message."""
    message = get_object_or_404(Message, id=message_id)
    if not message.to_recipients.filter(id=request.user.id).exists():
        raise PermissionDenied
    return redirect("messaging:new_conversation", message_id=message_id)


@login_required
def forward(request: HttpRequest, message_id: int) -> HttpResponse:
    """Transférer un message."""
    message = get_object_or_404(Message, id=message_id)
    return redirect("messaging:new_conversation", message_id=message_id)


@login_required
def save_draft(request: HttpRequest, message_id: int) -> HttpResponse:
    """Enregistrer un message comme brouillon."""
    message = get_object_or_404(Message, id=message_id)
    message.is_draft = True
    message.save()
    return redirect("messaging:drafts")


@login_required
def delete_message(request: HttpRequest, message_id: int) -> HttpResponse:
    """Supprimer un message (déplacement en corbeille)."""
    message = get_object_or_404(Message, id=message_id)
    message.deleted_at = timezone.now()
    message.save()
    return redirect("messaging:trash")


@login_required
def restore_message(request: HttpRequest, message_id: int) -> HttpResponse:
    """Restaurer un message supprimé."""
    message = get_object_or_404(Message, id=message_id)
    message.deleted_at = None
    message.save()
    return redirect("messaging:trash")


@login_required
def mark_read(request: HttpRequest, message_id: int) -> HttpResponse:
    """Marquer un message comme lu."""
    message = get_object_or_404(Message, id=message_id)
    if message.to_recipients.filter(id=request.user.id).exists():
        message.read_at = timezone.now()
        message.save()
    return redirect("messaging:inbox")


@login_required
@staff_required
def chat_list(request: HttpRequest) -> HttpResponse:
    return render(request, "messaging/chat_list.html", {"rows": _rows_for(request.user, ConversationKind.CHAT)})


@login_required
@staff_required
def new_chat(request: HttpRequest) -> HttpResponse:
    recipients_qs = (
        User.objects.filter(role__in=User.STAFF_ROLES)
        .exclude(id=request.user.id)
        .order_by("role", "last_name", "first_name")
    )

    if request.method == "POST":
        recipient_ids = request.POST.getlist("recipients")
        subject = (request.POST.get("subject") or "").strip()
        body = (request.POST.get("body") or "").strip()
        recipients = User.objects.filter(id__in=recipient_ids, role__in=User.STAFF_ROLES)

        if not recipients or not body:
            django_messages.error(request, "Destinataire(s) et message sont obligatoires.")
        elif recipients.count() > 1 and not subject:
            django_messages.error(request, "Un nom de groupe est requis pour un chat à plusieurs.")
        else:
            conversation = Conversation.objects.create(kind=ConversationKind.CHAT, subject=subject[:120])
            conversation.participants.add(request.user, *recipients)
            Message.objects.create(conversation=conversation, sender=request.user, body=body)
            django_messages.success(request, "Chat créé.")
            return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    return render(request, "messaging/new_chat.html", {"recipients": recipients_qs})


@login_required
def conversation_detail(request: HttpRequest, conversation_id: int) -> HttpResponse:
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related("participants", "messages__sender"), id=conversation_id
    )
    if not conversation.participants.filter(id=request.user.id).exists():
        raise PermissionDenied
    if conversation.kind == ConversationKind.CHAT and not request.user.is_staff_member:
        raise PermissionDenied

    if conversation.kind == ConversationKind.CHAT and request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if body:
            Message.objects.create(conversation=conversation, sender=request.user, body=body[:5000])
        return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    conversation.messages.filter(deleted_at__isnull=True).exclude(sender=request.user).filter(read_at__isnull=True).update(read_at=timezone.now())

    context = {
        "conversation": conversation,
        "others": conversation.participants.exclude(id=request.user.id),
        "message_list": conversation.messages.select_related("sender").all(),
    }
    return render(request, "messaging/conversation_detail.html", context)


@login_required
@require_POST
def send_message_ajax(request: HttpRequest, conversation_id: int) -> JsonResponse:
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    if conversation.kind == ConversationKind.CHAT and not request.user.is_staff_member:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)

    message = Message.objects.create(conversation=conversation, sender=request.user, body=body[:5000])
    return JsonResponse({
        "ok": True,
        "message": {
            "id": message.id,
            "sender": message.sender.get_full_name(),
            "sender_id": message.sender_id,
            "body": message.body,
            "sent_at": message.sent_at.strftime("%d/%m/%Y %H:%M"),
        },
    })
