from django.urls import path
from .views import (
    # Location
    MyLocationView,
    NearbyPeopleView,
    # Events
    EventListCreateView,
    EventDetailView,
    EventRSVPView,
    MyEventsView,
    EventAttendeesView,
    # Groups
    GroupListCreateView,
    GroupDetailView,
    GroupJoinView,
    GroupMembersView,
    GroupApproveMemberView,
    MyGroupsView,
    # Connections
    MyConnectionsView,
    SendConnectionRequestView,
    PendingRequestsView,
    RespondConnectionRequestView,
    WithdrawConnectionRequestView,
    RemoveConnectionView,
    # Meta
    CommunityActivityChoicesView,
)

urlpatterns = [
    # ── Reference data ────────────────────────────────────────────────────────
    path('activity-types/',                         CommunityActivityChoicesView.as_view(),    name='activity-types'),

    # ── Location & discovery ──────────────────────────────────────────────────
    path('location/',                               MyLocationView.as_view(),                  name='my-location'),
    path('nearby-people/',                          NearbyPeopleView.as_view(),                name='nearby-people'),

    # ── Events ────────────────────────────────────────────────────────────────
    path('events/',                                 EventListCreateView.as_view(),             name='event-list-create'),
    path('events/mine/',                            MyEventsView.as_view(),                    name='my-events'),
    path('events/<int:pk>/',                        EventDetailView.as_view(),                 name='event-detail'),
    path('events/<int:pk>/rsvp/',                   EventRSVPView.as_view(),                   name='event-rsvp'),
    path('events/<int:pk>/attendees/',              EventAttendeesView.as_view(),              name='event-attendees'),

    # ── Groups ────────────────────────────────────────────────────────────────
    path('groups/',                                 GroupListCreateView.as_view(),             name='group-list-create'),
    path('groups/mine/',                            MyGroupsView.as_view(),                    name='my-groups'),
    path('groups/<int:pk>/',                        GroupDetailView.as_view(),                 name='group-detail'),
    path('groups/<int:pk>/join/',                   GroupJoinView.as_view(),                   name='group-join'),
    path('groups/<int:pk>/members/',                GroupMembersView.as_view(),                name='group-members'),
    path('groups/<int:pk>/approve/<int:user_id>/',  GroupApproveMemberView.as_view(),          name='group-approve'),

    # ── Connections ───────────────────────────────────────────────────────────
    path('connections/',                            MyConnectionsView.as_view(),               name='my-connections'),
    path('connections/request/',                    SendConnectionRequestView.as_view(),       name='send-request'),
    path('connections/requests/',                   PendingRequestsView.as_view(),             name='pending-requests'),
    path('connections/requests/<int:pk>/respond/',  RespondConnectionRequestView.as_view(),    name='respond-request'),
    path('connections/requests/<int:pk>/',          WithdrawConnectionRequestView.as_view(),   name='withdraw-request'),
    path('connections/<int:user_id>/',              RemoveConnectionView.as_view(),            name='remove-connection'),
]
