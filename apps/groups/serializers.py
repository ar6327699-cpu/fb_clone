from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Group,
    GroupMember,
    GroupJoinRequest,
    GroupPoll,
    PollOption,
    PollVote,
)

User = get_user_model()

# =========================
# GROUP SERIALIZERS
# =========================

class GroupSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "group_type",
            "created_by",
            "created_at",
        )
        read_only_fields = ("created_by", "created_at")


class GroupMemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GroupMember
        fields = (
            "id",
            "group",
            "user",
            "role",
            "is_muted",
            "joined_at",
        )
        read_only_fields = ("role", "is_muted", "joined_at")


class GroupJoinRequestSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GroupJoinRequest
        fields = ("id", "group", "user", "created_at")
        read_only_fields = ("group", "user", "created_at")


# =========================
# POLL SERIALIZERS
# =========================

class PollOptionSerializer(serializers.ModelSerializer):
    votes = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ("id", "text", "votes")

    def get_votes(self, obj):
        return PollVote.objects.filter(option=obj).count()


class GroupPollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GroupPoll
        fields = (
            "id",
            "group",
            "question",
            "options",
            "created_by",
            "is_active",
            "created_at",
        )
        read_only_fields = ("group", "created_by", "created_at")

    def create(self, validated_data):
        options = validated_data.pop("options")

        poll = GroupPoll.objects.create(
            group=self.context["group"],
            created_by=self.context["request"].user,
            **validated_data
        )

        for opt in options:
            PollOption.objects.create(
                poll=poll,
                text=opt["text"]
            )

        return poll


class PollVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollVote
        fields = ("poll", "option")
