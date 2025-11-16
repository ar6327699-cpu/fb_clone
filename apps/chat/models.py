from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Chat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Chat {self.id}: {self.user1} & {self.user2}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')

    # text + media
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat/images/', null=True, blank=True)
    video = models.FileField(upload_to='chat/videos/', null=True, blank=True)
    audio = models.FileField(upload_to='chat/audio/', null=True, blank=True)

    # flags & receipts
    seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)
    edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_seen(self):
        if not self.seen:
            self.seen = True
            self.seen_at = timezone.now()
            self.save(update_fields=['seen', 'seen_at'])

    def soft_delete(self):
        self.is_deleted = True
        self.text = ""
        # remove media (optional: do not delete files from disk)
        self.image = None
        self.video = None
        self.audio = None
        self.save()

    def __str__(self):
        return f"{self.id} | {self.sender} → {self.receiver} | seen={self.seen}"


class Reaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self):
        return f"{self.user} reacted {self.emoji} on {self.message_id}"


class TypingStatus(models.Model):
    chat = models.ForeignKey(Chat, related_name="typing_status", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="typing_statuses", on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('chat', 'user')


class Block(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_made')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"
