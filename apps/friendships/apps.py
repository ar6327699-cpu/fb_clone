from django.apps import AppConfig

class FriendshipsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.friendships"
    label = "friendships"

    def ready(self):
        import apps.friendships.signals  # noqa: F401
