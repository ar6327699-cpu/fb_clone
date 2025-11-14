from django.db import models
from django.conf import settings

class Profile2(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    private = models.BooleanField(default=False)  # True = private, False = public

    def __str__(self):
        return f"{self.user.username}'s Profile"
