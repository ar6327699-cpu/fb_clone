from rest_framework import serializers
from .models import FriendRequest, Follower

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.ReadOnlyField(source='from_user.username')
    to_user = serializers.ReadOnlyField(source='to_user.username')

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'accepted', 'created_at']

class SendFriendRequestSerializer(serializers.ModelSerializer):
    to_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FriendRequest
        fields = ['to_user_id']

    def create(self, validated_data):
        from_user = self.context['request'].user
        to_user_id = validated_data['to_user_id']
        # Create friend request
        request_obj, created = FriendRequest.objects.get_or_create(
            from_user=from_user,
            to_user_id=to_user_id
        )
        # Add follower entry
        from .models import Follower
        Follower.objects.get_or_create(user_id=to_user_id, follower=from_user)
        return request_obj
