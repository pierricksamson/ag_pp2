from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("new/", views.new_conversation, name="new_conversation"),
    path("<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("<int:conversation_id>/send/", views.send_message_ajax, name="send_message_ajax"),
]
