from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

from apps.groups.models import GroupMember
from .models import GroupMessage
# =========================================================
# 🔹 PRIVATE CHAT CONSUMER (AS-IT-IS, UNCHANGED)
# =========================================================

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.room_group_name = f"chat_{self.thread_id}"
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        is_participant = await self.check_thread_participant()
        if not is_participant:
            await self.close()
            return

        is_blocked = await self.check_blocked()
        if is_blocked:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get("message", "")

            message = await self.save_message(message_text)

            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message_text,
                        "sender_id": self.user.id,
                        "message_id": message["id"],
                        "created_at": message["created_at"],
                    },
                )
        except Exception:
            await self.send(text_data=json.dumps({
                "error": "Failed to process message"
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender_id": event["sender_id"],
            "message_id": event["message_id"],
            "created_at": event["created_at"],
        }))

    @database_sync_to_async
    def check_thread_participant(self):
        from .models import ChatThread
        try:
            thread = ChatThread.objects.get(id=self.thread_id)
            return thread.users.filter(id=self.user.id).exists()
        except ChatThread.DoesNotExist:
            return False

    @database_sync_to_async
    def check_blocked(self):
        from .models import ChatThread, Block
        try:
            thread = ChatThread.objects.get(id=self.thread_id)
            other_user = thread.users.exclude(id=self.user.id).first()
            if other_user:
                return Block.objects.filter(
                    blocker=other_user, blocked=self.user
                ).exists()
            return False
        except ChatThread.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text):
        from .models import ChatThread, Message
        try:
            thread = ChatThread.objects.get(id=self.thread_id)
            message = Message.objects.create(
                thread=thread,
                sender=self.user,
                text=text
            )
            return {
                "id": message.id,
                "created_at": message.created_at.isoformat()
            }
        except Exception:
            return None


# =========================================================
# 🔥 GROUP CHAT CONSUMER (ADDED CLEANLY)
# =========================================================

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room_group_name = f"group_{self.group_id}"
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        if not await self.is_group_member():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type", "text")
            content = data.get("content", "")

            if await self.is_muted():
                return

            msg = await self.save_group_message(msg_type, content)

            if msg:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "group_message",
                        "id": msg["id"],
                        "sender_id": self.user.id,
                        "msg_type": msg_type,
                        "content": content,
                        "created_at": msg["created_at"],
                    }
                )
        except Exception:
            await self.send(text_data=json.dumps({
                "error": "Failed to process group message"
            }))

    async def group_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ---------------- DB HELPERS ----------------

    @database_sync_to_async
    def is_group_member(self):
        from apps.groups.models import GroupMember
        return GroupMember.objects.filter(
            group_id=self.group_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def is_muted(self):
        from apps.groups.models import GroupMember
        member = GroupMember.objects.filter(
            group_id=self.group_id,
            user=self.user
        ).first()
        return member.is_muted if member else True

    @database_sync_to_async
    def save_group_message(self, msg_type, content):
        from .models import GroupMessage

        data = {
            "group_id": self.group_id,
            "sender": self.user
        }

        if msg_type == "text":
            data["text"] = content
        elif msg_type == "image":
            data["image"] = content
        elif msg_type == "audio":
            data["audio"] = content
        elif msg_type == "video":
            data["video"] = content

        msg = GroupMessage.objects.create(**data)
        return {
            "id": msg.id,
            "created_at": msg.created_at.isoformat()
        }
    async def broadcast_delete(self, message_id):
     await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "group_delete",
            "message_id": message_id
        }
    )

    async def group_delete(self, event):
     await self.send(text_data=json.dumps({
        "type": "delete",
        "message_id": event["message_id"]
    }))

