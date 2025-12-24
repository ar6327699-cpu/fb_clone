from rest_framework import serializers
from .models import (
    Group, GroupMember,
    GroupPoll, PollOption, PollVote
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"
        read_only_fields = ("created_by", "created_at")


class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = "__all__"


# 🔥 POLL SERIALIZERS
class PollOptionSerializer(serializers.ModelSerializer):
    votes = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ("id", "text", "votes")

    def get_votes(self, obj):
        return PollVote.objects.filter(option=obj).count()


class GroupPollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True)

    class Meta:
        model = GroupPoll
        fields = ("id", "group", "question", "options", "is_active", "created_at")
        read_only_fields = ("group", "created_at")

    def create(self, validated_data):
        options = validated_data.pop("options")
        poll = GroupPoll.objects.create(**validated_data)

        for opt in options:
            PollOption.objects.create(poll=poll, text=opt["text"])

        return poll
