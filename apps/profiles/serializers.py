from rest_framework import serializers
from .models import Profile2

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile2
        fields = ['username', 'email', 'bio', 'profile_picture', 'location', 'private']
