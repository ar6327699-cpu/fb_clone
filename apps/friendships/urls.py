from django.urls import path
from .views import (
    SendFriendRequestView, AcceptFriendRequestView,
    FriendsListView, FollowersListView, FollowingListView
)

urlpatterns = [
    path('send/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('accept/', AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('friends/', FriendsListView.as_view(), name='friends_list'),
    path('followers/', FollowersListView.as_view(), name='followers_list'),
    path('following/', FollowingListView.as_view(), name='following_list'),
]
