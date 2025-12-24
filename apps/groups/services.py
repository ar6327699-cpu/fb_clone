from .models import GroupMember

def is_group_member(user, group_id):
    return GroupMember.objects.filter(
        user=user,
        group_id=group_id
    ).exists()
