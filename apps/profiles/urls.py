from django.urls import path
from .views import MyProfileView, ProfileDetailView

urlpatterns = [
    path('me/', MyProfileView.as_view(), name='my_profile'),
    path('<int:pk>/', ProfileDetailView.as_view(), name='profile_detail'),
]
