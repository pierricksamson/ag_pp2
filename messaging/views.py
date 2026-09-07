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
        last = c.messages.last()
        unread = c.messages.exclude(sender=user).filter(read_at__isnull=True).count()
        others = c.participants.exclude(id=user.id)
        rows.append({
            "conversation": c,
            "others": others,
            "last_message": last,
            "unread": unread,
        })
    rows.sort(key=lambda r: r["last_message"].sent_at if r["last_message"] else r["conversation"].created_at, reverse=True)
    return rows


# ---------- Mail ----------


@login_required
def inbox(request: HttpRequest) -> HttpResponse:
    return render(request, "messaging/inbox.html", {"rows": _rows_for(request.user, ConversationKind.MAIL)})


@login_required
def new_conversation(request: HttpRequest) -> HttpResponse:
    recipients_qs = User.objects.exclude(id=request.user.id).order_by("role", "last_name", "first_name")

    if request.method == "POST":
        recipient_ids = request.POST.getlist("recipients")
        subject = (request.POST.get("subject") or "").strip()
        body = (request.POST.get("body") or "").strip()

        if not recipient_ids or not body:
            django_messages.error(request, "Destinataire(s) et message sont obligatoires.")
        else:
            recipients = User.objects.filter(id__in=recipient_ids)
            conversation = Conversation.objects.create(kind=ConversationKind.MAIL, subject=subject[:120])
            conversation.participants.add(request.user, *recipients)
            Message.objects.create(conversation=conversation, sender=request.user, body=body)
            django_messages.success(request, "Message envoyé.")
            return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    return render(request, "messaging/new_conversation.html", {"recipients": recipients_qs})


# ---------- Chat (personnel uniquement : profs, administration, direction, vie scolaire…) ----------


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


# ---------- Détail (commun mail / chat) ----------


@login_required
def conversation_detail(request: HttpRequest, conversation_id: int) -> HttpResponse:
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related("participants", "messages__sender"), id=conversation_id
    )
    if not conversation.participants.filter(id=request.user.id).exists():
        raise PermissionDenied
    if conversation.kind == ConversationKind.CHAT and not request.user.is_staff_member:
        raise PermissionDenied

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if body:
            Message.objects.create(conversation=conversation, sender=request.user, body=body[:5000])
        return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    # Marquer comme lus les messages reçus.
    conversation.messages.exclude(sender=request.user).filter(read_at__isnull=True).update(read_at=timezone.now())

    context = {
        "conversation": conversation,
        "others": conversation.participants.exclude(id=request.user.id),
        "message_list": conversation.messages.select_related("sender").all(),
    }
    return render(request, "messaging/conversation_detail.html", context)


# ---------- API : envoi AJAX ----------


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
