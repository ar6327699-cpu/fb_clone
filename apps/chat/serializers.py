from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message, Reaction, Block, TypingStatus

User = get_user_model()

class ReactionSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Reaction
        fields = ['id', 'message', 'user', 'user_username', 'emoji', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'user_username']


class MessageSerializer(serializers.ModelSerializer):
    reactions = ReactionSerializer(many=True, read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'sender_username', 'receiver', 'receiver_username',
            'text', 'image', 'video', 'audio',
            'seen', 'seen_at', 'edited', 'is_deleted', 'created_at', 'updated_at',
            'reactions'
        ]
        read_only_fields = [
            'id', 'sender', 'seen', 'seen_at', 'edited', 'is_deleted', 'created_at',
            'updated_at', 'reactions'
        ]
        extra_kwargs = {
            'text': {'required': False, 'allow_blank': True},
            'image': {'required': False, 'allow_null': True},
            'video': {'required': False, 'allow_null': True},
            'audio': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        if 'image' in validated_data:
            instance.image = validated_data.get('image')
        if 'video' in validated_data:
            instance.video = validated_data.get('video')
        if 'audio' in validated_data:
            instance.audio = validated_data.get('audio')
        instance.edited = True
        instance.save()
        return instance



class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    other_user_id = serializers.SerializerMethodField()
    other_username = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "user1", "user2", "created_at", "last_message", "other_user_id", "other_username"]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return MessageSerializer(last, context=self.context).data if last else None

    def get_other_user_id(self, obj):
        request_user = self.context.get('request_user')
        if not request_user:
            return None
        return obj.user2.id if obj.user1 == request_user else obj.user1.id

    def get_other_username(self, obj):
        request_user = self.context.get('request_user')
        if not request_user:
            return None
        other = obj.user2 if obj.user1 == request_user else obj.user1
        return getattr(other, 'username', None)


class BlockSerializer(serializers.ModelSerializer):
    blocked_username = serializers.CharField(source='blocked.username', read_only=True)
    class Meta:
        model = Block
        fields = ['id', 'blocker', 'blocked', 'blocked_username', 'created_at']
        read_only_fields = ['blocker', 'created_at']


class TypingStatusSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = TypingStatus
        fields = ['id', 'chat', 'user', 'user_username', 'is_typing', 'updated_at']
        read_only_fields = ['id', 'user_username', 'updated_at']
