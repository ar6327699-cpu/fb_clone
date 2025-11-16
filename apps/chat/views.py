from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser 
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Chat, Message, Block, Reaction, TypingStatus
from .serializers import ChatSerializer, MessageSerializer, BlockSerializer, ReactionSerializer, TypingStatusSerializer
from .utils import can_send_message, is_blocked, are_friends

User = get_user_model()


def get_or_create_chat(user1, user2):
    chat = Chat.objects.filter(
        (Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1))
    ).first()
    if not chat:
        chat = Chat.objects.create(user1=user1, user2=user2)
    return chat


class CreateChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        target_id = request.data.get("user_id")
        if not target_id:
            return Response({"error": "user_id required"}, status=400)

        target_user = get_object_or_404(User, id=target_id)

        # Block checks
        if is_blocked(request.user, target_user):
            return Response({"error": "Cannot create chat — block exists between users."}, status=403)

        # Privacy check via util
        allowed, reason = can_send_message(request.user, target_user)
        if not allowed:
            return Response({"error": reason}, status=403)

        chat = get_or_create_chat(request.user, target_user)
        serializer = ChatSerializer(chat, context={'request_user': request.user, 'request': request})
        return Response(serializer.data, status=201)


class SendMessageView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # handles text + media

    def post(self, request, *args, **kwargs):
        chat_id = request.data.get("chat")
        receiver_id = request.data.get("receiver")  # required
        text = request.data.get("text")  # optional
        image = request.FILES.get("image")  # optional
        video = request.FILES.get("video")  # optional
        audio = request.FILES.get("audio")  # optional

        # validation
        if not chat_id or not receiver_id:
            return Response({"error": "chat and receiver are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({"error": "Chat does not exist"}, status=status.HTTP_404_NOT_FOUND)

        # create message
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            receiver_id=receiver_id,
            text=text or "",
            image=image,
            video=video,
            audio=audio
        )

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ChatMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)

        # participant check
        if request.user != chat.user1 and request.user != chat.user2:
            return Response({"error": "Not allowed"}, status=403)

        # If there is a block where one user blocked the other, do not return chat messages
        other = chat.user1 if chat.user2 == request.user else chat.user2
        if is_blocked(request.user, other):
            return Response({"error": "Chat is unavailable due to block."}, status=403)

        # mark all messages received by request.user as seen (update seen_at)
        unseen = Message.objects.filter(chat=chat, receiver=request.user, seen=False)
        now = timezone.now()
        unseen.update(seen=True, seen_at=now)

        messages = Message.objects.filter(chat=chat).order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)


class ChatListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # fetch chats where user is participant
        chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).order_by("-created_at")

        result = []
        for chat in chats:
            other = chat.user2 if chat.user1 == request.user else chat.user1

            # exclude if block exists between them (either direction)
            if is_blocked(request.user, other):
                continue

            last_message = chat.messages.order_by("-created_at").first()
            unseen_count = chat.messages.filter(receiver=request.user, seen=False).count()

            result.append({
                "chat_id": chat.id,
                "other_user_id": other.id,
                "other_username": getattr(other, 'username', None),
                "last_message": (last_message.text if last_message and not last_message.is_deleted else
                                 ("This message was deleted" if last_message and last_message.is_deleted else "")),
                "unseen_count": unseen_count,
                "chat_created_at": chat.created_at,
            })

        return Response(result)


class GlobalUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_unread = Message.objects.filter(receiver=request.user, seen=False).count()
        return Response({"unread_count": total_unread})


class EditMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)

        if message.sender != request.user:
            return Response({"error": "You can edit only your own messages."}, status=403)

        serializer = MessageSerializer(message, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()  # will set edited=True in serializer.update
        return Response(MessageSerializer(message).data)


class DeleteMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        # allow sender to delete their message (soft delete)
        if message.sender != request.user:
            return Response({"error": "You can delete only your own messages."}, status=403)

        message.soft_delete()
        return Response({"success": "Message deleted."})


class DeleteChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user != chat.user1 and request.user != chat.user2:
            return Response({"error": "Not allowed"}, status=403)

        chat.delete()
        return Response({"success": "Chat deleted."})


# ---------- Block / Unblock endpoints ----------

class BlockUserView(generics.CreateAPIView):
    serializer_class = BlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        blocked_id = request.data.get("blocked")
        if not blocked_id:
            return Response({"error": "blocked required"}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate block
        if Block.objects.filter(blocker=request.user, blocked_id=blocked_id).exists():
            return Response({"error": "User already blocked"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(blocker=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnblockUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blocked_id = request.data.get("blocked_id")
        if not blocked_id:
            return Response({"error": "blocked_id required"}, status=400)

        user_to_unblock = get_object_or_404(User, id=blocked_id)
        deleted, _ = Block.objects.filter(blocker=request.user, blocked=user_to_unblock).delete()
        if deleted:
            return Response({"success": "User unblocked."})
        return Response({"detail": "No block existed."}, status=200)


class BlockListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blocks = Block.objects.filter(blocker=request.user)
        data = [{"blocked_id": b.blocked.id, "blocked_username": getattr(b.blocked, 'username', None), "created_at": b.created_at} for b in blocks]
        return Response(data)


# ---------- Reactions ----------

class ReactionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message')
        emoji = request.data.get('emoji')
        if not message_id or not emoji:
            return Response({"error": "message and emoji required"}, status=400)

        msg = get_object_or_404(Message, id=message_id)

        # ensure participant
        if request.user not in [msg.chat.user1, msg.chat.user2]:
            return Response({"error": "Not allowed"}, status=403)

        reaction, created = Reaction.objects.update_or_create(
            message=msg, user=request.user,
            defaults={'emoji': emoji}
        )
        return Response(ReactionSerializer(reaction).data, status=201 if created else 200)


class ReactionDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message_id = request.data.get('message')
        if not message_id:
            return Response({"error": "message required"}, status=400)
        msg = get_object_or_404(Message, id=message_id)
        Reaction.objects.filter(message=msg, user=request.user).delete()
        return Response({"deleted": True})


# ---------- Typing indicator ----------

class TypingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        chat_id = request.data.get('chat_id')
        is_typing = request.data.get('is_typing', 'false')
        is_typing_bool = str(is_typing).lower() in ('1', 'true', 'yes')
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user not in [chat.user1, chat.user2]:
            return Response({"error": "Not allowed"}, status=403)
        ts, _ = TypingStatus.objects.update_or_create(chat=chat, user=request.user, defaults={'is_typing': is_typing_bool})
        return Response(TypingStatusSerializer(ts).data)


# ---------- Mark seen and last seen ----------

class MarkSeenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user not in [chat.user1, chat.user2]:
            return Response({"error": "Not allowed"}, status=403)
        now = timezone.now()
        qs = Message.objects.filter(chat=chat, receiver=request.user, seen=False)
        count = qs.count()
        qs.update(seen=True, seen_at=now)
        return Response({"updated": count})


class UpdateLastSeenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # try to write to profile.last_seen if exists, else noop
        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            profile.last_seen = timezone.now()
            profile.save(update_fields=['last_seen'])
            return Response({"last_seen": profile.last_seen})
        # fallback: simply return success
        return Response({"updated": True})
