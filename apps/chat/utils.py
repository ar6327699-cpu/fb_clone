from django.contrib.auth import get_user_model
from .models import Block
from apps.accounts.models import Profile  # if you have a Profile model for privacy
from apps.friendships.models import FriendRequest, Follower

User = get_user_model()

def are_friends(user1, user2):
    """
    Check if two users are friends (both accepted each other's friend request).
    """
    return FriendRequest.objects.filter(
        from_user=user1, to_user=user2, accepted=True
    ).exists() or FriendRequest.objects.filter(
        from_user=user2, to_user=user1, accepted=True
    ).exists()


def is_blocked(user_a, user_b):
    """
    Returns True if user_a blocked user_b OR user_b blocked user_a.
    """
    return Block.objects.filter(blocker=user_a, blocked=user_b).exists() or \
           Block.objects.filter(blocker=user_b, blocked=user_a).exists()


# apps/chat/utils.py

def can_send_message(sender, receiver):
    """
    Check if sender can send a message to receiver.
    Returns (allowed: bool, reason: str)
    """
    # Get the receiver's profile2 safely
    profile = getattr(receiver, 'profile2', None)

    if not profile:
        return False, "Receiver has no profile."
    
    if profile.private:
        return False, "Cannot send message to a private profile."
    
    # Add more conditions here if needed, e.g., blocking, friendship, etc.
    
    return True, "Message can be sent."
