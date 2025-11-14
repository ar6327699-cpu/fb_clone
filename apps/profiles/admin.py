from django.contrib import admin
from .models import Profile2

@admin.register(Profile2)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'location', 'private')  # columns to show
    list_filter = ('private',)  # filter by private/public profiles
    search_fields = ('user__username', 'bio', 'location')  # search profiles by username or bio
