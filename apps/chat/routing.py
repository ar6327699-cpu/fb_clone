from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<thread_id>\d+)/$", ChatConsumer.as_asgi()),
]
from django.urls import re_path
from .consumers import ChatConsumer, GroupChatConsumer

websocket_urlpatterns = [
    # 🔹 Private chat (1-to-1)
    re_path(
        r"ws/chat/(?P<thread_id>\d+)/$",
        ChatConsumer.as_asgi()
    ),

    # 🔥 Group chat
    re_path(
        r"ws/groups/(?P<group_id>\d+)/$",
        GroupChatConsumer.as_asgi()
    ),
]
