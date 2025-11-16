from django.contrib import admin
from django.urls import path, include
from core.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    #just  created for  the testing okay
    path("health/", health, name="health"),
    #calling the  api of the user acc login, logout, reg
    path("api/accounts/", include("apps.accounts.urls", namespace="accounts")),
     path("api/chat/", include("apps.chat.urls", namespace="chat")),
]
