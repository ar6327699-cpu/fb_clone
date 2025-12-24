from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.room_group_name = f"chat_{self.thread_id}"
        self.user = self.scope.get("user")

        # Check if user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Check if user is part of the thread
        is_participant = await self.check_thread_participant()
        if not is_participant:
            await self.close()
            return

        # Check if user is blocked
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
            
            # Save message to database
            message = await self.save_message(message_text)
            
            if message:
                # Send message to room group
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
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": "Failed to process message"
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
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
