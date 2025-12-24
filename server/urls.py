from django.contrib import admin
from django.urls import path, include
from core.views import health
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    #just  created for  the testing okay
    path("health/", health, name="health"),
    #calling the  api of the user acc login, logout, reg
    path("api/accounts/", include("apps.accounts.urls", namespace="accounts")),
    #calling the apis of the Friendship
    path("api/friendships/", include("apps.friendships.urls", namespace="friendships")),
    #calling  the apis of the feed
    path("api/feed/", include("apps.feed.urls", namespace="feed")),
    #calling the api of the comments and the likes
    path("api/comments/", include("apps.comments.urls", namespace="comments")),
    path("api/likes/", include("apps.likes.urls", namespace="likes")),
    #calling the  api of the communities
    path("api/communities/", include("apps.communities.urls", namespace="communities")),
    #for the calling of the communities post  (like, unlike etc)
    path("api/posts/", include("apps.communities.posts_urls")), 
    #for the chat code api calling 
    path("api/chat/", include("apps.chat.urls", namespace="chat")),
# calling the api of the groups
path("api/groups/", include("apps.groups.urls", namespace="groups")),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
