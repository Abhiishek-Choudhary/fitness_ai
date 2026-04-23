from django.urls import path
from . import views

urlpatterns = [
    # Gym CRUD
    path('', views.GymListCreateView.as_view(), name='gym-list-create'),
    path('nearby/', views.NearbyGymsView.as_view(), name='gym-nearby'),
    path('my-gyms/', views.MyGymsView.as_view(), name='gym-my-gyms'),
    path('inbox/', views.UserCampaignInboxView.as_view(), name='gym-campaign-inbox'),
    path('<int:pk>/', views.GymDetailView.as_view(), name='gym-detail'),

    # Media gallery
    path('<int:pk>/media/', views.GymMediaUploadView.as_view(), name='gym-media-upload'),
    path('media/<int:media_id>/', views.GymMediaDeleteView.as_view(), name='gym-media-delete'),

    # Follow / membership
    path('<int:pk>/follow/', views.GymFollowToggleView.as_view(), name='gym-follow'),
    path('<int:pk>/members/', views.GymMembersListView.as_view(), name='gym-members'),
    path('<int:pk>/members/<int:user_id>/upgrade/', views.GymUpgradeMemberView.as_view(), name='gym-member-upgrade'),

    # Messaging
    path('<int:pk>/messages/', views.GymMessageView.as_view(), name='gym-messages'),
    path('<int:pk>/conversations/', views.GymConversationsView.as_view(), name='gym-conversations'),

    # Email campaigns
    path('<int:pk>/campaigns/', views.GymCampaignSendView.as_view(), name='gym-campaign-send'),
    path('<int:pk>/campaigns/list/', views.GymCampaignListView.as_view(), name='gym-campaign-list'),
]
