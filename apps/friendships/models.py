from django.db import models
from django.conf import settings

class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='received_requests', on_delete=models.CASCADE
    )
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} | Accepted: {self.accepted}"

class Follower(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE
    )
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'follower')

    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"
