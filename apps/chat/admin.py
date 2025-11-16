from django.contrib import admin
from .models import Chat, Message, Block, Reaction, TypingStatus

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')
    search_fields = ('user1__username', 'user2__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'chat', 'sender', 'receiver',
        'short_text', 'has_image', 'has_video', 'has_audio',
        'seen', 'edited', 'is_deleted', 'created_at', 'updated_at'
    )
    list_filter = ('seen', 'edited', 'is_deleted', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'text')

    def short_text(self, obj):
        return obj.text[:30] + "..." if obj.text else ""

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True

    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True

    def has_audio(self, obj):
        return bool(obj.audio)
    has_audio.boolean = True


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'emoji', 'created_at')
    search_fields = ('user__username', 'emoji', 'message__text')


@admin.register(TypingStatus)
class TypingStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'user', 'is_typing', 'updated_at')
    list_filter = ('is_typing',)
    search_fields = ('user__username',)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
