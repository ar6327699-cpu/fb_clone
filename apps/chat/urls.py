from django.urls import path
from .views import (
    CreateChatView, SendMessageView, ChatMessagesView, ChatListView,
    GlobalUnreadCountView, EditMessageView, DeleteMessageView, DeleteChatView,
    BlockUserView, UnblockUserView, BlockListView,
    ReactionCreateView, ReactionDeleteView,
    TypingView, MarkSeenView, UpdateLastSeenView
)

app_name = "chat"

urlpatterns = [
    path("create/", CreateChatView.as_view(), name="create_chat"),
    path("send/", SendMessageView.as_view(), name="send_message"),
    path("messages/<int:chat_id>/", ChatMessagesView.as_view(), name="get_messages"),
    path("list/", ChatListView.as_view(), name="chat_list"),
    path("unread/", GlobalUnreadCountView.as_view(), name="global_unread"),

    # message operations
    path("edit/<int:message_id>/", EditMessageView.as_view(), name="edit_message"),
    path("delete-message/<int:message_id>/", DeleteMessageView.as_view(), name="delete_message"),
    path("delete-chat/<int:chat_id>/", DeleteChatView.as_view(), name="delete_chat"),

    # block endpoints
    path("block/", BlockUserView.as_view(), name="block_user"),
    path("unblock/", UnblockUserView.as_view(), name="unblock_user"),
    path("blocks/", BlockListView.as_view(), name="block_list"),

    # reactions
    path("reaction/", ReactionCreateView.as_view(), name="reaction_create"),
    path("reaction/delete/", ReactionDeleteView.as_view(), name="reaction_delete"),

    # typing + seen + last_seen
    path("typing/", TypingView.as_view(), name="typing"),
    path("mark-seen/<int:chat_id>/", MarkSeenView.as_view(), name="mark_seen"),
    path("last-seen/", UpdateLastSeenView.as_view(), name="update_last_seen"),
]
