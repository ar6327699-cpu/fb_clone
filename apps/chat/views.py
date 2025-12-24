from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.friendships.models import Friendship
from apps.accounts.models import User
from .models import (
    ChatThread, ChatRequest, Message, MessageDeletion, Block
)
from .serializers import (
    ChatRequestSerializer, MessageSerializer, ChatThreadSerializer
)
from .permissions import is_blocked

#importing for the helper function
from django.db.models import Q

#just the helper function

def are_friends(user1, user2):
    return Friendship.objects.filter(
        Q(user=user1, friend=user2) |
        Q(user=user2, friend=user1)
    ).exists()

#updated request chat function
class SendChatRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        to_user = get_object_or_404(User, id=user_id)

        if to_user == request.user:
            return Response({"detail": "Cannot chat with yourself"}, status=400)

        # ✅ Correct friendship check
        if are_friends(request.user, to_user):
            # Check if chat thread already exists
            thread = ChatThread.objects.filter(
                users=request.user
            ).filter(
                users=to_user
            ).first()

            if not thread:
                thread = ChatThread.objects.create()
                thread.users.add(request.user, to_user)

            return Response(
                {
                    "detail": "Already friends. Chat available.",
                    "thread_id": thread.id
                },
                status=200
            )

        # If not friends → send chat request
        chat_request, created = ChatRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )

        if not created:
            return Response(
                {"detail": "Chat request already sent"},
                status=400
            )

        return Response(
            ChatRequestSerializer(chat_request).data,
            status=201
        )

#updated request accept function
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

        # Prevent duplicate threads
        thread = ChatThread.objects.filter(
            users=chat_request.from_user
        ).filter(
            users=chat_request.to_user
        ).first()

        if not thread:
            thread = ChatThread.objects.create()
            thread.users.add(
                chat_request.from_user,
                chat_request.to_user
            )

        return Response(
            {
                "detail": "Chat request accepted",
                "thread_id": thread.id
            }
        )


class MessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id, users=request.user)
        messages = thread.messages.exclude(
            deleted_for__user=request.user
        )
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
        message = get_object_or_404(Message, id=message_id)
        MessageDeletion.objects.get_or_create(
            message=message, user=request.user
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


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        Block.objects.get_or_create(
            blocker=request.user, blocked=user
        )
        return Response({"detail": "User blocked"})


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        Block.objects.filter(
            blocker=request.user, blocked_id=user_id
        ).delete()
        return Response({"detail": "User unblocked"})


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


class ChatThreadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threads = ChatThread.objects.filter(users=request.user).order_by('-created_at')
        return Response(ChatThreadSerializer(threads, many=True, context={'request': request}).data)


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


class BlockedUsersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .serializers import BlockSerializer
        blocks = Block.objects.filter(blocker=request.user)
        return Response(BlockSerializer(blocks, many=True).data)


class MarkMessageAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        from django.utils import timezone
        message = get_object_or_404(Message, id=message_id)
        
        # Only the receiver can mark as read
        if message.sender == request.user:
            return Response({"detail": "Cannot mark your own message as read"}, status=400)
        
        # Check if user is part of the thread
        if not message.thread.users.filter(id=request.user.id).exists():
            return Response({"detail": "Not authorized"}, status=403)
        
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
        return Response({"detail": "Message marked as read"})
