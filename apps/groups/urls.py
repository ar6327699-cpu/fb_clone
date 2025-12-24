from django.urls import path
from .views import *
app_name = "groups"

urlpatterns = [
    # 🔹 GROUP CORE
    path("create/", CreateGroupView.as_view()),
    path("<int:group_id>/join/", JoinGroupView.as_view()),
    path("<int:group_id>/approve/<int:user_id>/", ApproveJoinView.as_view()),
    path("<int:group_id>/remove/<int:user_id>/", RemoveMemberView.as_view()),
    path("<int:group_id>/mute/<int:user_id>/", MuteMemberView.as_view()),
    path("<int:group_id>/delete/", DeleteGroupView.as_view()),

    # 🔥 POLLING
    path("<int:group_id>/polls/", GroupPollListView.as_view()),
    path("<int:group_id>/polls/create/", CreatePollView.as_view()),
    path("polls/<int:poll_id>/vote/<int:option_id>/", VotePollView.as_view()),
    path("polls/<int:poll_id>/close/", ClosePollView.as_view()),
]
