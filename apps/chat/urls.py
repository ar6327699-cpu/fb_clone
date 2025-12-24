from django.urls import path
from .views import (
    SendChatRequestView,
    AcceptChatRequestView,
    RejectChatRequestView,
    MessageListCreateView,
    DeleteMessageForMeView,
    DeleteMessageForEveryoneView,
    BlockUserView,
    UnblockUserView,
    ChatThreadListView,
    PendingChatRequestsView,
    BlockedUsersListView,
    MarkMessageAsReadView,
)

app_name = "chat"

urlpatterns = [
    # Chat requests
    path("requests/send/<int:user_id>/", SendChatRequestView.as_view(), name="send_request"),
    path("requests/accept/<int:pk>/", AcceptChatRequestView.as_view(), name="accept_request"),
    path("requests/reject/<int:pk>/", RejectChatRequestView.as_view(), name="reject_request"),
    path("requests/pending/", PendingChatRequestsView.as_view(), name="pending_requests"),

    # Chat threads
    path("threads/", ChatThreadListView.as_view(), name="thread_list"),
    path("threads/<int:thread_id>/messages/", MessageListCreateView.as_view(), name="thread_messages"),

    # Messages
    path("messages/<int:message_id>/delete-me/", DeleteMessageForMeView.as_view(), name="delete_for_me"),
    path("messages/<int:message_id>/delete-everyone/", DeleteMessageForEveryoneView.as_view(), name="delete_for_everyone"),
    path("messages/<int:message_id>/mark-read/", MarkMessageAsReadView.as_view(), name="mark_read"),

    # Blocking
    path("block/<int:user_id>/", BlockUserView.as_view(), name="block_user"),
    path("unblock/<int:user_id>/", UnblockUserView.as_view(), name="unblock_user"),
    path("blocked/", BlockedUsersListView.as_view(), name="blocked_list"),
]
