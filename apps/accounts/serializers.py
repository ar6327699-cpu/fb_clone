from rest_framework import serializers
from django.contrib.auth import authenticate, password_validation
from datetime import date
from .models import User
from apps.profiles.models import Profile

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")

#controlling the functions of the register user
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password2", "first_name", "last_name")
        extra_kwargs = {"email": {"required": True}}

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        password_validation.validate_password(
            password=data["password"],
            user=User(**{k: data.get(k) for k in ("username", "email", "first_name", "last_name")})
        )
        return data

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

#controlling the function of the login user
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Unable to authenticate with provided credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data["user"] = user
        return data

#creating the function of the profile viewing
class ProfileSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = ("bio", "dob", "gender", "avatar", "age")

    def validate_dob(self, value):
        if value is None:
            return value
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("You must be at least 13 years old.")
        return value

#creating the function of the removing the acc
class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user
        password = data.get("password")
        if not authenticate(username=user.username, password=password):
            raise serializers.ValidationError("Password is incorrect.")
        return data
