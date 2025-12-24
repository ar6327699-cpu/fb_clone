from django.contrib import admin
from .models import Group, GroupMember, GroupJoinRequest

admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(GroupJoinRequest)
