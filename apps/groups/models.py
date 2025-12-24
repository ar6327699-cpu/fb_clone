from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    GROUP_TYPE = (
        ("public", "Public"),
        ("private", "Private"),
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    group_type = models.CharField(max_length=10, choices=GROUP_TYPE, default="public")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE = (
        ("admin", "Admin"),
        ("member", "Member"),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE)
    is_muted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")


class GroupJoinRequest(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")


# 🔥 POLLS
class GroupPoll(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="polls")
    question = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PollOption(models.Model):
    poll = models.ForeignKey(GroupPoll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=200)


class PollVote(models.Model):
    poll = models.ForeignKey(GroupPoll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("poll", "user")
