from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Group,
    GroupMember,
    GroupJoinRequest,
    GroupPoll,
    PollOption,
    PollVote,
)
from .serializers import GroupSerializer, GroupPollSerializer
from .permissions import IsGroupAdmin, IsGroupMember
class CreateGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save(created_by=request.user)

        GroupMember.objects.create(
            group=group,
            user=request.user,
            role="admin"
        )
        return Response(serializer.data, status=201)


class JoinGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)

        if group.group_type == "private":
            GroupJoinRequest.objects.get_or_create(
                group=group,
                user=request.user
            )
            return Response({"detail": "Join request sent"})

        GroupMember.objects.get_or_create(
            group=group,
            user=request.user,
            role="member"
        )
        return Response({"detail": "Joined group"})


class ApproveJoinView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, group_id, user_id):
        GroupJoinRequest.objects.filter(
            group_id=group_id,
            user_id=user_id
        ).delete()

        GroupMember.objects.create(
            group_id=group_id,
            user_id=user_id,
            role="member"
        )
        return Response({"detail": "Approved"})


class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, group_id, user_id):
        GroupMember.objects.filter(
            group_id=group_id,
            user_id=user_id
        ).delete()
        return Response({"detail": "Member removed"})


class MuteMemberView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, group_id, user_id):
        GroupMember.objects.filter(
            group_id=group_id,
            user_id=user_id
        ).update(is_muted=True)
        return Response({"detail": "Member muted"})


class DeleteGroupView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def delete(self, request, group_id):
        Group.objects.filter(id=group_id).delete()
        return Response({"detail": "Group deleted"})
class CreatePollView(APIView):
    permission_classes = [IsAuthenticated, IsGroupMember]

    def post(self, request, group_id):
        serializer = GroupPollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        poll = serializer.save(
            group_id=group_id,
            created_by=request.user
        )

        return Response(GroupPollSerializer(poll).data, status=201)
class GroupPollListView(APIView):
    permission_classes = [IsAuthenticated, IsGroupMember]

    def get(self, request, group_id):
        polls = GroupPoll.objects.filter(group_id=group_id)
        serializer = GroupPollSerializer(polls, many=True)
        return Response(serializer.data)
class VotePollView(APIView):
    permission_classes = [IsAuthenticated, IsGroupMember]

    def post(self, request, poll_id, option_id):
        poll = get_object_or_404(GroupPoll, id=poll_id, is_active=True)

        PollVote.objects.get_or_create(
            poll=poll,
            option_id=option_id,
            user=request.user
        )

        return Response({"detail": "Vote submitted"})
class ClosePollView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, poll_id):
        poll = get_object_or_404(GroupPoll, id=poll_id)
        poll.is_active = False
        poll.save()
        return Response({"detail": "Poll closed"})
