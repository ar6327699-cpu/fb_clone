from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.db.models import Q

from apps.friendships.models import Friendship
from apps.accounts.models import User
from apps.groups.models import Group, GroupMember
from .models import GroupMessage, GroupMessageSeen

from .models import (
    ChatThread,
    ChatRequest,
    Message,
    MessageDeletion,
    Block,
    GroupMessage, GroupMessageSeen
)
from .serializers import (
    ChatRequestSerializer,
    MessageSerializer,
    ChatThreadSerializer
)
from .permissions import is_blocked


# =========================================================
# 🔹 HELPERS
# =========================================================

def are_friends(user1, user2):
    return Friendship.objects.filter(
        Q(user=user1, friend=user2) |
        Q(user=user2, friend=user1)
    ).exists()


# =========================================================
# 🔹 CHAT REQUESTS
# =========================================================

class SendChatRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        to_user = get_object_or_404(User, id=user_id)

        if to_user == request.user:
            return Response({"detail": "Cannot chat with yourself"}, status=400)

        if are_friends(request.user, to_user):
            thread = ChatThread.objects.filter(
                users=request.user
            ).filter(users=to_user).first()

            if not thread:
                thread = ChatThread.objects.create()
                thread.users.add(request.user, to_user)

            return Response({
                "detail": "Already friends. Chat available.",
                "thread_id": thread.id
            })

        chat_request, created = ChatRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )

        if not created:
            return Response({"detail": "Chat request already sent"}, status=400)

        return Response(ChatRequestSerializer(chat_request).data, status=201)


class AcceptChatRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        chat_request = get_object_or_404(
            ChatRequest,
            id=pk,
            to_user=request.user,
            is_accepted__isnull=True
        )

        chat_request.is_accepted = True
        chat_request.save()

        thread = ChatThread.objects.filter(
            users=chat_request.from_user
        ).filter(users=chat_request.to_user).first()

        if not thread:
            thread = ChatThread.objects.create()
            thread.users.add(chat_request.from_user, chat_request.to_user)

        return Response({
            "detail": "Chat request accepted",
            "thread_id": thread.id
        })


class RejectChatRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        chat_request = get_object_or_404(
            ChatRequest,
            id=pk,
            to_user=request.user,
            is_accepted__isnull=True
        )
        chat_request.is_accepted = False
        chat_request.save()
        return Response({"detail": "Chat request rejected"})


# =========================================================
# 🔹 PRIVATE MESSAGES
# =========================================================

class MessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id, users=request.user)
        messages = thread.messages.exclude(deleted_for__user=request.user)
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id, users=request.user)
        receiver = thread.users.exclude(id=request.user.id).first()

        if is_blocked(request.user, receiver):
            return Response({"detail": "You are blocked"}, status=403)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, thread=thread)
        return Response(serializer.data, status=201)


class DeleteMessageForMeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        MessageDeletion.objects.get_or_create(
            message_id=message_id,
            user=request.user
        )
        return Response({"detail": "Deleted for you"})


class DeleteMessageForEveryoneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, sender=request.user)

        if not message.can_delete_for_everyone():
            return Response({"detail": "Time expired"}, status=403)

        message.is_deleted = True
        message.save()
        return Response({"detail": "Deleted for everyone"})


class MarkMessageAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        from django.utils import timezone

        message = get_object_or_404(Message, id=message_id)

        if message.sender == request.user:
            return Response({"detail": "Cannot mark your own message as read"}, status=400)

        if not message.thread.users.filter(id=request.user.id).exists():
            return Response({"detail": "Not authorized"}, status=403)

        message.is_read = True
        message.read_at = timezone.now()
        message.save()

        return Response({"detail": "Message marked as read"})


# =========================================================
# 🔹 THREADS & BLOCKS
# =========================================================

class ChatThreadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threads = ChatThread.objects.filter(users=request.user).order_by("-created_at")
        return Response(
            ChatThreadSerializer(threads, many=True, context={"request": request}).data
        )


class PendingChatRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        received = ChatRequest.objects.filter(
            to_user=request.user,
            is_accepted__isnull=True
        )
        sent = ChatRequest.objects.filter(
            from_user=request.user,
            is_accepted__isnull=True
        )
        return Response({
            "received": ChatRequestSerializer(received, many=True).data,
            "sent": ChatRequestSerializer(sent, many=True).data
        })


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        Block.objects.get_or_create(blocker=request.user, blocked=user)
        return Response({"detail": "User blocked"})


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        Block.objects.filter(blocker=request.user, blocked_id=user_id).delete()
        return Response({"detail": "User unblocked"})


class BlockedUsersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .serializers import BlockSerializer
        blocks = Block.objects.filter(blocker=request.user)
        return Response(BlockSerializer(blocks, many=True).data)


# =========================================================
# 🔥 GROUP MEDIA UPLOAD
# =========================================================

class UploadGroupMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"detail": "No file provided"}, status=400)

        path = default_storage.save(f"group_media/{file.name}", file)
        return Response({"url": default_storage.url(path)}, status=201)


# =========================================================
# 🔥 GROUP MESSAGE HISTORY
# =========================================================

class GroupMessageHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        if not GroupMember.objects.filter(
            group_id=group_id,
            user=request.user
        ).exists():
            return Response(
                {"detail": "Not a group member"},
                status=403
            )

        messages = GroupMessage.objects.filter(
            group_id=group_id
        ).order_by("-created_at")[:50]

        total_members = GroupMember.objects.filter(
            group_id=group_id
        ).count() - 1  # exclude sender

        data = []
        for msg in messages:
            seen_count = msg.seen_by.count()

            data.append({
                "id": msg.id,
                "sender_id": msg.sender_id,

                "text": None if msg.is_deleted else msg.text,
                "image": None if msg.is_deleted else (msg.image.url if msg.image else None),
                "audio": None if msg.is_deleted else (msg.audio.url if msg.audio else None),
                "video": None if msg.is_deleted else (msg.video.url if msg.video else None),

                "is_deleted": msg.is_deleted,

                # 🔥 SEEN INFO
                "seen_count": seen_count,
                "seen_by_all": seen_count >= max(total_members, 0),

                "created_at": msg.created_at,
            })

        return Response(data)

# =========================================================
# 🔥 GROUP MESSAGE DELETE
# =========================================================

class DeleteGroupMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(GroupMessage, id=message_id)

        member = GroupMember.objects.filter(
            group=message.group,
            user=request.user
        ).first()

        if not member:
            return Response({"detail": "Not a group member"}, status=403)

        if message.sender != request.user and member.role != "admin":
            return Response({"detail": "Not allowed"}, status=403)

        message.is_deleted = True
        message.save()

        return Response({"detail": "Message deleted"})



class MarkGroupMessageSeenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(GroupMessage, id=message_id)

        # must be group member
        if not GroupMember.objects.filter(
            group=message.group,
            user=request.user
        ).exists():
            return Response({"detail": "Not a group member"}, status=403)

        # sender does not mark own message
        if message.sender_id == request.user.id:
            return Response({"detail": "Sender cannot mark seen"}, status=400)

        obj, created = GroupMessageSeen.objects.get_or_create(
            message=message,
            user=request.user
        )

        if not created:
            return Response({"detail": "Already seen"})

        return Response({
            "detail": "Seen marked",
            "message_id": message.id,
            "user_id": request.user.id
        })
    
    

class GroupMessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)

        if not GroupMember.objects.filter(
            group=group,
            user=request.user
        ).exists():
            return Response(
                {"detail": "Not a group member"},
                status=403
            )

        message = GroupMessage.objects.create(
            group=group,
            sender=request.user,
            text=request.data.get("text", ""),
            image=request.data.get("image"),
            audio=request.data.get("audio"),
            video=request.data.get("video"),
        )

        return Response(
            {
                "id": message.id,
                "group_id": group.id,
                "sender_id": request.user.id,
                "created_at": message.created_at
            },
            status=201
        )