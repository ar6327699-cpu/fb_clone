from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.friendships.models import Friendship
from .models import ChatThread, ChatRequest, Message, Block,GroupMessage, GroupMessageSeen
from apps.groups.models import Group, GroupMember

User = get_user_model()


class ChatRequestTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass123"
        )
        self.client.force_authenticate(user=self.user1)

    def test_send_chat_request_non_friends(self):
        """Test sending chat request to non-friend"""
        response = self.client.post(f"/chat/requests/send/{self.user2.id}/")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ChatRequest.objects.filter(
                from_user=self.user1, to_user=self.user2
            ).exists()
        )

    def test_send_chat_request_already_friends(self):
        """Test sending chat request to existing friend creates thread"""
        # Create friendship
        Friendship.objects.create(user=self.user1, friend=self.user2)
        
        response = self.client.post(f"/chat/requests/send/{self.user2.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("thread_id", response.data)

    def test_accept_chat_request(self):
        """Test accepting a chat request"""
        chat_request = ChatRequest.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        
        response = self.client.post(f"/chat/requests/accept/{chat_request.id}/")
        self.assertEqual(response.status_code, 200)
        
        chat_request.refresh_from_db()
        self.assertTrue(chat_request.is_accepted)
        self.assertIn("thread_id", response.data)

    def test_reject_chat_request(self):
        """Test rejecting a chat request"""
        chat_request = ChatRequest.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        
        response = self.client.post(f"/chat/requests/reject/{chat_request.id}/")
        self.assertEqual(response.status_code, 200)
        
        chat_request.refresh_from_db()
        self.assertFalse(chat_request.is_accepted)


class BlockingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass123"
        )
        self.client.force_authenticate(user=self.user1)

    def test_block_user(self):
        """Test blocking a user"""
        response = self.client.post(f"/chat/block/{self.user2.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Block.objects.filter(blocker=self.user1, blocked=self.user2).exists()
        )

    def test_unblock_user(self):
        """Test unblocking a user"""
        Block.objects.create(blocker=self.user1, blocked=self.user2)
        
        response = self.client.post(f"/chat/unblock/{self.user2.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Block.objects.filter(blocker=self.user1, blocked=self.user2).exists()
        )

    def test_blocked_user_cannot_send_message(self):
        """Test that blocked user cannot send messages"""
        # Create thread
        thread = ChatThread.objects.create()
        thread.users.add(self.user1, self.user2)
        
        # User1 blocks User2
        Block.objects.create(blocker=self.user1, blocked=self.user2)
        
        # User2 tries to send message
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f"/chat/threads/{thread.id}/messages/",
            {"text": "Hello"}
        )
        self.assertEqual(response.status_code, 403)


class MessageTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass123"
        )
        self.thread = ChatThread.objects.create()
        self.thread.users.add(self.user1, self.user2)
        self.client.force_authenticate(user=self.user1)

    def test_send_message(self):
        """Test sending a message"""
        response = self.client.post(
            f"/chat/threads/{self.thread.id}/messages/",
            {"text": "Hello, World!"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 1)

    def test_delete_message_for_me(self):
        """Test deleting message for self"""
        message = Message.objects.create(
            thread=self.thread, sender=self.user1, text="Test"
        )
        
        response = self.client.post(f"/chat/messages/{message.id}/delete-me/")
        self.assertEqual(response.status_code, 200)

    def test_delete_message_for_everyone(self):
        """Test deleting message for everyone within time limit"""
        message = Message.objects.create(
            thread=self.thread, sender=self.user1, text="Test"
        )
        
        response = self.client.post(f"/chat/messages/{message.id}/delete-everyone/")
        self.assertEqual(response.status_code, 200)
        
        message.refresh_from_db()
        self.assertTrue(message.is_deleted)

    def test_mark_message_as_read(self):
        """Test marking message as read"""
        message = Message.objects.create(
            thread=self.thread, sender=self.user2, text="Test"
        )
        
        response = self.client.post(f"/chat/messages/{message.id}/mark-read/")
        self.assertEqual(response.status_code, 200)
        
        message.refresh_from_db()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)


class ChatThreadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="pass123"
        )
        self.thread = ChatThread.objects.create()
        self.thread.users.add(self.user1, self.user2)
        self.client.force_authenticate(user=self.user1)

    def test_list_chat_threads(self):
        """Test listing all chat threads"""
        response = self.client.get("/chat/threads/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_pending_chat_requests(self):
        """Test listing pending chat requests"""
        ChatRequest.objects.create(from_user=self.user2, to_user=self.user1)
        
        response = self.client.get("/chat/requests/pending/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["received"]), 1)
        self.assertEqual(len(response.data["sent"]), 0)
class GroupChatTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # users
        self.admin = User.objects.create_user(
            username="admin", email="admin@test.com", password="pass123"
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="pass123"
        )
        self.other = User.objects.create_user(
            username="other", email="other@test.com", password="pass123"
        )

        # group
        self.group = Group.objects.create(
            name="Test Group",
            created_by=self.admin
        )

        # members
        GroupMember.objects.create(
            group=self.group,
            user=self.admin,
            role="admin"
        )
        GroupMember.objects.create(
            group=self.group,
            user=self.member,
            role="member"
        )

        self.client.force_authenticate(user=self.admin)

    # =====================================================
    # GROUP MESSAGE HISTORY
    # =====================================================

    def test_group_message_history_as_member(self):
        GroupMessage.objects.create(
            group=self.group,
            sender=self.admin,
            text="Hello group"
        )

        response = self.client.get(
            f"/chat/groups/{self.group.id}/messages/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_group_message_history_non_member_forbidden(self):
        self.client.force_authenticate(user=self.other)

        response = self.client.get(
            f"/chat/groups/{self.group.id}/messages/"
        )
        self.assertEqual(response.status_code, 403)

    # =====================================================
    # GROUP MESSAGE SEND
    # =====================================================

    def test_group_member_can_send_message(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.post(
            f"/chat/groups/{self.group.id}/messages/",
            {"text": "Hi everyone"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GroupMessage.objects.count(), 1)

    def test_non_member_cannot_send_message(self):
        self.client.force_authenticate(user=self.other)

        response = self.client.post(
            f"/chat/groups/{self.group.id}/messages/",
            {"text": "Should fail"}
        )
        self.assertEqual(response.status_code, 403)

    # =====================================================
    # GROUP MESSAGE DELETE
    # =====================================================

    def test_sender_can_delete_group_message(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.member,
            text="Delete me"
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/chat/group-messages/{msg.id}/delete/"
        )
        self.assertEqual(response.status_code, 200)

        msg.refresh_from_db()
        self.assertTrue(msg.is_deleted)

    def test_admin_can_delete_any_group_message(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.member,
            text="Admin delete"
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/chat/group-messages/{msg.id}/delete/"
        )
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_delete_others_message(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.admin,
            text="Protected"
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/chat/group-messages/{msg.id}/delete/"
        )
        self.assertEqual(response.status_code, 403)

    # =====================================================
    # GROUP MESSAGE SEEN
    # =====================================================

    def test_mark_group_message_seen(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.admin,
            text="Seen test"
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/chat/group-messages/{msg.id}/seen/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GroupMessageSeen.objects.count(), 1)

    def test_seen_only_once(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.admin,
            text="Seen once"
        )

        self.client.force_authenticate(user=self.member)
        self.client.post(f"/chat/group-messages/{msg.id}/seen/")
        response = self.client.post(f"/chat/group-messages/{msg.id}/seen/")

        self.assertEqual(GroupMessageSeen.objects.count(), 1)
        self.assertEqual(response.status_code, 400)

    def test_non_member_cannot_mark_seen(self):
        msg = GroupMessage.objects.create(
            group=self.group,
            sender=self.admin,
            text="No access"
        )

        self.client.force_authenticate(user=self.other)
        response = self.client.post(
            f"/chat/group-messages/{msg.id}/seen/"
        )
        self.assertEqual(response.status_code, 403)