from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class ChatThread(models.Model):
    users = models.ManyToManyField(User, related_name="chat_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatThread {self.id}"


class ChatRequest(models.Model):
    from_user = models.ForeignKey(
        User, related_name="sent_chat_requests", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="received_chat_requests", on_delete=models.CASCADE
    )
    is_accepted = models.BooleanField(null=True)  # None = pending
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")


class Block(models.Model):
    blocker = models.ForeignKey(
        User, related_name="blocked_users", on_delete=models.CASCADE
    )
    blocked = models.ForeignKey(
        User, related_name="blocked_by", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "blocked")


class Message(models.Model):
    thread = models.ForeignKey(
        ChatThread, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat/images/", blank=True, null=True)
    audio = models.FileField(upload_to="chat/audio/", blank=True, null=True)
    video = models.FileField(upload_to="chat/video/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def can_delete_for_everyone(self):
        return timezone.now() <= self.created_at + timedelta(minutes=10)


class MessageDeletion(models.Model):
    message = models.ForeignKey(
        Message, related_name="deleted_for", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("message", "user")
