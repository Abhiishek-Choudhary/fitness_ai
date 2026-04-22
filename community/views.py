from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from .models import (
    UserLocation, FitnessEvent, EventAttendee,
    CommunityGroup, GroupMember, ConnectionRequest, UserConnection,
)
from .permissions import IsOrganizerOrReadOnly, IsGroupAdminOrReadOnly
from .serializers import (
    UserLocationSerializer,
    EventCardSerializer, EventDetailSerializer, EventCreateSerializer, RSVPSerializer,
    GroupCardSerializer, GroupDetailSerializer, GroupCreateSerializer, GroupMemberSerializer,
    NearbyPersonSerializer,
    ConnectionRequestSerializer, SendConnectionRequestSerializer,
    RespondRequestSerializer, ConnectedUserSerializer,
)
from .services import event_service, group_service, connection_service


class CommunityPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50


# ── Location ───────────────────────────────────────────────────────────────────

class MyLocationView(APIView):
    """GET / PUT  /api/community/location/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            loc = request.user.location
            return Response(UserLocationSerializer(loc).data)
        except UserLocation.DoesNotExist:
            return Response({}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request):
        try:
            loc = request.user.location
            serializer = UserLocationSerializer(loc, data=request.data, partial=True)
        except UserLocation.DoesNotExist:
            serializer = UserLocationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)


# ── People Discovery ───────────────────────────────────────────────────────────

class NearbyPeopleView(APIView):
    """
    GET /api/community/nearby-people/
    Query params: radius_km (default 50), activity
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            radius = float(request.query_params.get('radius_km', 50))
            radius = min(max(radius, 1), 200)
        except ValueError:
            radius = 50

        try:
            people = connection_service.get_nearby_people(
                user=request.user,
                radius_km=radius,
                activity=request.query_params.get('activity'),
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = NearbyPersonSerializer(people, many=True)
        return Response({'count': len(people), 'radius_km': radius, 'results': serializer.data})


# ── Events ─────────────────────────────────────────────────────────────────────

class EventListCreateView(APIView):
    """
    GET  /api/community/events/
    POST /api/community/events/
    Query params: activity_type, city, lat, lon, radius_km, from_date
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius_km = float(request.query_params.get('radius_km', 50))
        activity = request.query_params.get('activity_type')
        city = request.query_params.get('city')

        if lat and lon:
            try:
                events = event_service.get_nearby_events(float(lat), float(lon), radius_km, activity)
            except ValueError:
                return Response({'error': 'Invalid lat/lon.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            events = list(event_service.get_public_events(activity_type=activity, city=city))

        paginator = CommunityPagination()
        page = paginator.paginate_queryset(events, request)
        serializer = EventCardSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = event_service.create_event(request.user, serializer.validated_data)
        return Response(EventDetailSerializer(event, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """GET / PUT / DELETE  /api/community/events/<id>/"""
    permission_classes = [IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]

    def _get_event(self, pk):
        try:
            return FitnessEvent.objects.select_related(
                'organizer', 'organizer__creator_profile'
            ).get(pk=pk)
        except FitnessEvent.DoesNotExist:
            return None

    def get(self, request, pk):
        event = self._get_event(pk)
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EventDetailSerializer(event, context={'request': request}).data)

    def put(self, request, pk):
        event = self._get_event(pk)
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, event)
        serializer = EventCreateSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(EventDetailSerializer(event, context={'request': request}).data)

    def delete(self, request, pk):
        event = self._get_event(pk)
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, event)
        try:
            event_service.cancel_event(event, request.user)
        except (PermissionError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Event cancelled.'})


class EventRSVPView(APIView):
    """POST /api/community/events/<id>/rsvp/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = FitnessEvent.objects.get(pk=pk)
        except FitnessEvent.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RSVPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = event_service.rsvp_event(event, request.user, serializer.validated_data['rsvp_status'])
        except (ValueError, PermissionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class MyEventsView(APIView):
    """GET /api/community/events/mine/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = event_service.get_user_events(request.user)
        return Response({
            'organised': EventCardSerializer(data['organised'], many=True, context={'request': request}).data,
            'attending': EventCardSerializer(data['attending'], many=True, context={'request': request}).data,
        })


class EventAttendeesView(APIView):
    """GET /api/community/events/<id>/attendees/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            event = FitnessEvent.objects.get(pk=pk)
        except FitnessEvent.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        from .serializers import UserMiniSerializer
        going = EventAttendee.objects.filter(
            event=event, rsvp_status='going'
        ).select_related('user', 'user__fitness_profile', 'user__creator_profile')
        return Response({
            'going_count': going.count(),
            'attendees': UserMiniSerializer([a.user for a in going[:50]], many=True).data,
        })


# ── Groups ─────────────────────────────────────────────────────────────────────

class GroupListCreateView(APIView):
    """GET / POST  /api/community/groups/"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = group_service.get_groups(
            activity_focus=request.query_params.get('activity_focus'),
            city=request.query_params.get('city'),
            search=request.query_params.get('search'),
        )
        paginator = CommunityPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = GroupCardSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = group_service.create_group(request.user, serializer.validated_data)
        return Response(GroupDetailSerializer(group, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class GroupDetailView(APIView):
    """GET / PUT  /api/community/groups/<id>/"""
    permission_classes = [IsAuthenticatedOrReadOnly, IsGroupAdminOrReadOnly]

    def _get_group(self, pk):
        try:
            return CommunityGroup.objects.select_related('creator').get(pk=pk)
        except CommunityGroup.DoesNotExist:
            return None

    def get(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GroupDetailSerializer(group, context={'request': request}).data)

    def put(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, group)
        serializer = GroupCreateSerializer(group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(GroupDetailSerializer(group, context={'request': request}).data)


class GroupJoinView(APIView):
    """POST /api/community/groups/<id>/join/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            group = CommunityGroup.objects.get(pk=pk)
        except CommunityGroup.DoesNotExist:
            return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = group_service.join_group(group, request.user)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(result)


class GroupMembersView(APIView):
    """GET /api/community/groups/<id>/members/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            group = CommunityGroup.objects.get(pk=pk)
        except CommunityGroup.DoesNotExist:
            return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)

        members = GroupMember.objects.filter(
            group=group, status='active'
        ).select_related('user', 'user__fitness_profile', 'user__creator_profile').order_by('joined_at')

        paginator = CommunityPagination()
        page = paginator.paginate_queryset(members, request)
        return paginator.get_paginated_response(GroupMemberSerializer(page, many=True).data)


class GroupApproveMemberView(APIView):
    """POST /api/community/groups/<id>/approve/<user_id>/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, user_id):
        try:
            group = CommunityGroup.objects.get(pk=pk)
            target = User.objects.get(pk=user_id)
        except (CommunityGroup.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            group_service.approve_member(group, request.user, target)
        except (PermissionError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': f'{target.username} approved.'})


class MyGroupsView(APIView):
    """GET /api/community/groups/mine/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = group_service.get_user_groups(request.user)
        return Response(GroupCardSerializer(groups, many=True, context={'request': request}).data)


# ── Connections ────────────────────────────────────────────────────────────────

class MyConnectionsView(APIView):
    """GET /api/community/connections/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = connection_service.get_connections(request.user)
        return Response(ConnectedUserSerializer(users, many=True).data)


class SendConnectionRequestView(APIView):
    """POST /api/community/connections/request/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            receiver = User.objects.get(pk=data['receiver_id'])
            req = connection_service.send_connection_request(
                request.user, receiver, data.get('message', '')
            )
        except (User.DoesNotExist, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ConnectionRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class PendingRequestsView(APIView):
    """GET /api/community/connections/requests/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        received = connection_service.get_pending_received(request.user)
        sent = connection_service.get_pending_sent(request.user)
        return Response({
            'received': ConnectionRequestSerializer(received, many=True).data,
            'sent': ConnectionRequestSerializer(sent, many=True).data,
        })


class RespondConnectionRequestView(APIView):
    """POST /api/community/connections/requests/<id>/respond/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            req = ConnectionRequest.objects.get(pk=pk)
        except ConnectionRequest.DoesNotExist:
            return Response({'error': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RespondRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = connection_service.respond_to_request(req, request.user, serializer.validated_data['accept'])
        except (PermissionError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'accepted': result['accepted']})


class WithdrawConnectionRequestView(APIView):
    """DELETE /api/community/connections/requests/<id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            req = ConnectionRequest.objects.get(pk=pk)
        except ConnectionRequest.DoesNotExist:
            return Response({'error': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            connection_service.withdraw_request(req, request.user)
        except (PermissionError, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemoveConnectionView(APIView):
    """DELETE /api/community/connections/<user_id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        try:
            other = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            connection_service.remove_connection(request.user, other)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityActivityChoicesView(APIView):
    """GET /api/community/activity-types/ — public reference data."""
    permission_classes = [AllowAny]

    def get(self, request):
        from .models import ACTIVITY_CHOICES, DIFFICULTY_CHOICES
        return Response({
            'activity_types': [{'value': k, 'label': v} for k, v in ACTIVITY_CHOICES],
            'difficulty_levels': [{'value': k, 'label': v} for k, v in DIFFICULTY_CHOICES],
        })
