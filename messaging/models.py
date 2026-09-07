from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(
        "users.User", related_name="conversations"
    )
    subject = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject or f"Conversation #{self.pk}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("sent_at",)

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"