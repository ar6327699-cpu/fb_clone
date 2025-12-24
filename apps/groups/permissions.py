from rest_framework.permissions import BasePermission
from .models import GroupMember


class IsGroupMember(BasePermission):
    def has_permission(self, request, view):
        return GroupMember.objects.filter(
            group_id=view.kwargs.get("group_id"),
            user=request.user
        ).exists()


class IsGroupAdmin(BasePermission):
    def has_permission(self, request, view):
        return GroupMember.objects.filter(
            group_id=view.kwargs.get("group_id"),
            user=request.user,
            role="admin"
        ).exists()
