from .models import Block


def is_blocked(sender, receiver):
    return Block.objects.filter(
        blocker=receiver, blocked=sender
    ).exists()
