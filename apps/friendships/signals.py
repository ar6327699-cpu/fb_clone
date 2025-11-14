from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FriendRequest, Follower

@receiver(post_save, sender=FriendRequest)
def create_mutual_follow_on_accept(sender, instance, created, **kwargs):
    """
    When a FriendRequest is accepted, create mutual following.
    """
    if not created and instance.accepted:
        # Add reverse following if not exists
        Follower.objects.get_or_create(user=instance.from_user, follower=instance.to_user)
