from django.contrib import admin
from .models import FriendRequest, Follower

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')

@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ('follower', 'user', 'created_at')
    search_fields = ('follower__username', 'user__username')
