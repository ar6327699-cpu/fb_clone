from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Profile
from .serializers import ProfileSerializer
from apps.friendships.models import FriendRequest  # adjust according to your friendship app

class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class ProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_object(self):
        profile = super().get_object()
        user = self.request.user

        # Private profile check
        if profile.private and user != profile.user:
            # Check if the requesting user is a friend
            if not profile.user.friendship_set.filter(friends=user).exists():
                raise PermissionDenied("This profile is private.")
        return profile
