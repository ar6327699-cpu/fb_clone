from django.db import models
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework import status
from .models import FriendRequest, Follower
from .serializers import FriendRequestSerializer, SendFriendRequestSerializer

# Serializer for followers/following
class FollowerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    follower = serializers.StringRelatedField()

    class Meta:
        model = Follower
        fields = ['user', 'follower', 'created_at']

# Send friend request
class SendFriendRequestView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendFriendRequestSerializer

# Accept friend request
class AcceptFriendRequestView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer
    queryset = FriendRequest.objects.all()

    def update(self, request, *args, **kwargs):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        friend_request.accepted = True
        friend_request.save()

        # Add mutual following
        Follower.objects.get_or_create(user=friend_request.from_user, follower=friend_request.to_user)

        return Response({"detail": "Friend request accepted, now friends"}, status=status.HTTP_200_OK)

# List friends
class FriendsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(
            accepted=True
        ).filter(
            models.Q(from_user=user) | models.Q(to_user=user)
        )

# List followers
class FollowersListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowerSerializer

    def get_queryset(self):
        user = self.request.user
        return Follower.objects.filter(user=user)

# List following
class FollowingListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowerSerializer

    def get_queryset(self):
        user = self.request.user
        return Follower.objects.filter(follower=user)
