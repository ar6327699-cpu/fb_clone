from rest_framework import serializers
from .models import (
    ChatThread, ChatRequest, Message, MessageDeletion, Block
)
from apps.accounts.serializers import UserMiniSerializer


class ChatRequestSerializer(serializers.ModelSerializer):
    from_user = UserMiniSerializer(read_only=True)
    to_user = UserMiniSerializer(read_only=True)

    class Meta:
        model = ChatRequest
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ("sender", "created_at", "thread", "is_read", "read_at")

    # 🔥 THIS IS THE IMPORTANT PART (DELETE FOR EVERYONE)
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.is_deleted:
            data["text"] = "🚫 This message was deleted"
            data["image"] = None
            data["audio"] = None
            data["video"] = None

        return data


class ChatThreadSerializer(serializers.ModelSerializer):
    users = UserMiniSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ("id", "users", "created_at", "last_message", "other_user", "unread_count")

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        return MessageSerializer(msg).data if msg else None

    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other_user = obj.users.exclude(id=request.user.id).first()
            return UserMiniSerializer(other_user).data if other_user else None
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0


class BlockSerializer(serializers.ModelSerializer):
    blocked = UserMiniSerializer(read_only=True)

    class Meta:
        model = Block
        fields = ("id", "blocked", "created_at")
