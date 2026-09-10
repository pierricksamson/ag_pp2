from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("sent/", views.sent, name="sent"),
    path("drafts/", views.drafts, name="drafts"),
    path("trash/", views.trash, name="trash"),
    path("new/", views.new_conversation, name="new_conversation"),
    path("new/<int:message_id>/", views.new_conversation, name="new_conversation_from_message"),
    path("chat/", views.chat_list, name="chat_list"),
    path("chat/new/", views.new_chat, name="new_chat"),
    path("<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("<int:conversation_id>/send/", views.send_message_ajax, name="send_message_ajax"),
    path("<int:message_id>/delete/", views.delete_message, name="delete_message"),
    path("<int:message_id>/restore/", views.restore_message, name="restore_message"),
    path("<int:message_id>/mark-read/", views.mark_read, name="mark_read"),
    path("<int:message_id>/save-draft/", views.save_draft, name="save_draft"),
    path("<int:message_id>/reply/", views.reply, name="reply"),
    path("<int:message_id>/reply-all/", views.reply_all, name="reply_all"),
    path("<int:message_id>/forward/", views.forward, name="forward"),
    path("draft/auto-save/", views.draft_auto_save, name="draft_auto_save"),
    path("bulk-action/", views.bulk_action, name="bulk_action"),
]
