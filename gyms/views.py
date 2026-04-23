from django.db.models import Max, Count, Q
from django.contrib.auth.models import User as DjangoUser
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Gym, GymMedia, GymMembership, GymMessage, GymEmailCampaign
from .serializers import (
    GymCardSerializer,
    GymDetailSerializer,
    GymCreateUpdateSerializer,
    GymMediaSerializer,
    GymMembershipSerializer,
    GymMessageSerializer,
    GymMessageCreateSerializer,
    GymCampaignCreateSerializer,
    GymCampaignListSerializer,
)
from .services import gym_service, email_service


# ── Gym registration & listing ─────────────────────────────────────────────────

class GymListCreateView(APIView):
    """
    GET  /api/gyms/  — browse all active gyms
    POST /api/gyms/  — register a new gym (authenticated)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = Gym.objects.filter(is_active=True).select_related('owner')

        gym_type = request.query_params.get('gym_type')
        city = request.query_params.get('city')
        verified = request.query_params.get('is_verified')

        if gym_type:
            qs = qs.filter(gym_type=gym_type)
        if city:
            qs = qs.filter(city__icontains=city)
        if verified is not None:
            qs = qs.filter(is_verified=(verified.lower() == 'true'))

        serializer = GymCardSerializer(qs, many=True, context={'request': request})
        return Response({'count': qs.count(), 'results': serializer.data})

    def post(self, request):
        serializer = GymCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gym = serializer.save(owner=request.user)
        return Response(
            GymDetailSerializer(gym, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GymDetailView(APIView):
    """
    GET    /api/gyms/<id>/  — public gym profile
    PUT    /api/gyms/<id>/  — full update (owner only)
    PATCH  /api/gyms/<id>/  — partial update (owner only)
    DELETE /api/gyms/<id>/  — deactivate (owner only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _get_gym(self, pk):
        try:
            return Gym.objects.select_related('owner').prefetch_related('media').get(pk=pk)
        except Gym.DoesNotExist:
            return None

    def get(self, request, pk):
        gym = self._get_gym(pk)
        if not gym:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GymDetailSerializer(gym, context={'request': request}).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        gym = self._get_gym(pk)
        if not gym:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can edit this gym.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = GymCreateUpdateSerializer(gym, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        gym = serializer.save()
        return Response(GymDetailSerializer(gym, context={'request': request}).data)

    def delete(self, request, pk):
        gym = self._get_gym(pk)
        if not gym:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can delete this gym.'}, status=status.HTTP_403_FORBIDDEN)
        gym.is_active = False
        gym.save(update_fields=['is_active'])
        return Response({'message': 'Gym deactivated successfully.'})


class MyGymsView(generics.ListAPIView):
    """GET /api/gyms/my-gyms/ — gyms owned by the authenticated user."""
    permission_classes = [IsAuthenticated]
    serializer_class = GymDetailSerializer

    def get_queryset(self):
        return Gym.objects.filter(owner=self.request.user).prefetch_related('media')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


# ── Nearby discovery ───────────────────────────────────────────────────────────

class NearbyGymsView(APIView):
    """
    GET /api/gyms/nearby/?lat=<>&lon=<>&radius=<>&gym_type=<>
    Returns gyms sorted by distance ascending, each with distance_km.
    """

    def get(self, request):
        try:
            lat = float(request.query_params['lat'])
            lon = float(request.query_params['lon'])
        except (KeyError, ValueError):
            return Response(
                {'error': 'lat and lon are required numeric query parameters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius_km = float(request.query_params.get('radius', 10))
        gym_type = request.query_params.get('gym_type')

        gyms = gym_service.get_nearby_gyms(lat, lon, radius_km, gym_type=gym_type)
        serializer = GymCardSerializer(gyms, many=True, context={'request': request})
        return Response({'count': len(gyms), 'radius_km': radius_km, 'results': serializer.data})


# ── Gallery media ──────────────────────────────────────────────────────────────

class GymMediaUploadView(APIView):
    """POST /api/gyms/<id>/media/ — owner uploads gallery image."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            gym = Gym.objects.get(pk=pk)
        except Gym.DoesNotExist:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can upload media.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GymMediaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(gym=gym)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GymMediaDeleteView(APIView):
    """DELETE /api/gyms/media/<media_id>/ — owner removes gallery image."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, media_id):
        try:
            media = GymMedia.objects.select_related('gym__owner').get(pk=media_id)
        except GymMedia.DoesNotExist:
            return Response({'error': 'Media not found.'}, status=status.HTTP_404_NOT_FOUND)
        if media.gym.owner != request.user:
            return Response({'error': 'Only the gym owner can delete media.'}, status=status.HTTP_403_FORBIDDEN)
        media.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Follow / membership ────────────────────────────────────────────────────────

class GymFollowToggleView(APIView):
    """
    POST /api/gyms/<id>/follow/
    Follows if not following, unfollows if already following.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            gym = Gym.objects.get(pk=pk, is_active=True)
        except Gym.DoesNotExist:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner == request.user:
            return Response({'error': 'Owners cannot follow their own gym.'}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = gym_service.toggle_follow(request.user, gym)
        if membership is None:
            return Response({'following': False, 'message': 'Unfollowed.'})
        return Response(
            {'following': True, 'message': 'Now following.', 'status': membership.status},
            status=status.HTTP_201_CREATED,
        )


class GymMembersListView(generics.ListAPIView):
    """GET /api/gyms/<id>/members/ — list of followers and members."""
    serializer_class = GymMembershipSerializer

    def get_queryset(self):
        return GymMembership.objects.filter(
            gym_id=self.kwargs['pk']
        ).select_related('user', 'gym')


class GymUpgradeMemberView(APIView):
    """
    POST /api/gyms/<id>/members/<user_id>/upgrade/
    Gym owner upgrades a follower to 'member' status.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, user_id):
        try:
            gym = Gym.objects.get(pk=pk)
        except Gym.DoesNotExist:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can upgrade members.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            membership = gym_service.upgrade_to_member(gym, user_id)
        except GymMembership.DoesNotExist:
            return Response({'error': 'This user is not following the gym.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(GymMembershipSerializer(membership).data)


# ── Messaging ──────────────────────────────────────────────────────────────────

class GymMessageView(APIView):
    """
    GET  /api/gyms/<id>/messages/            — user reads their thread with this gym
    GET  /api/gyms/<id>/messages/?user_id=<> — owner reads a specific user's thread
    POST /api/gyms/<id>/messages/            — send a message
    """
    permission_classes = [IsAuthenticated]

    def _get_gym(self, pk):
        try:
            return Gym.objects.get(pk=pk)
        except Gym.DoesNotExist:
            return None

    def get(self, request, pk):
        gym = self._get_gym(pk)
        if not gym:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_owner = gym.owner == request.user

        if is_owner:
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'Pass ?user_id=<id> to view a specific conversation.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            messages = GymMessage.objects.filter(
                gym=gym, conversation_user_id=user_id
            ).select_related('sender')
        else:
            messages = GymMessage.objects.filter(
                gym=gym, conversation_user=request.user
            ).select_related('sender')
            messages.filter(is_from_owner=True, is_read=False).update(is_read=True)

        return Response(GymMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        gym = self._get_gym(pk)
        if not gym:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GymMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_owner = gym.owner == request.user

        if is_owner:
            user_id = request.data.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'Pass user_id to specify which user you are replying to.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                convo_user = DjangoUser.objects.get(pk=user_id)
            except DjangoUser.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

            msg = GymMessage.objects.create(
                gym=gym,
                conversation_user=convo_user,
                sender=request.user,
                content=serializer.validated_data['content'],
                is_from_owner=True,
            )
        else:
            msg = GymMessage.objects.create(
                gym=gym,
                conversation_user=request.user,
                sender=request.user,
                content=serializer.validated_data['content'],
                is_from_owner=False,
            )

        return Response(GymMessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class GymConversationsView(APIView):
    """
    GET /api/gyms/<id>/conversations/
    Owner-only: summary list of all user threads, sorted by most recent.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            gym = Gym.objects.get(pk=pk)
        except Gym.DoesNotExist:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can view all conversations.'}, status=status.HTTP_403_FORBIDDEN)

        threads = (
            GymMessage.objects
            .filter(gym=gym)
            .values('conversation_user')
            .annotate(
                last_message_at=Max('created_at'),
                unread_count=Count('id', filter=Q(is_from_owner=False, is_read=False)),
            )
            .order_by('-last_message_at')
        )

        result = []
        for thread in threads:
            user = DjangoUser.objects.get(pk=thread['conversation_user'])
            last_msg = (
                GymMessage.objects
                .filter(gym=gym, conversation_user=user)
                .order_by('-created_at')
                .values_list('content', flat=True)
                .first()
            )
            result.append({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                },
                'last_message': last_msg or '',
                'last_message_at': thread['last_message_at'],
                'unread_count': thread['unread_count'],
            })

        return Response(result)


# ── Email campaigns ────────────────────────────────────────────────────────────

class GymCampaignSendView(APIView):
    """
    POST /api/gyms/<id>/campaigns/
    Owner-only: create and immediately send an email campaign.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            gym = Gym.objects.get(pk=pk)
        except Gym.DoesNotExist:
            return Response({'error': 'Gym not found.'}, status=status.HTTP_404_NOT_FOUND)
        if gym.owner != request.user:
            return Response({'error': 'Only the gym owner can send campaigns.'}, status=status.HTTP_403_FORBIDDEN)
        if not gym.latitude or not gym.longitude:
            return Response(
                {'error': 'Set the gym location (latitude + longitude) before sending campaigns.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GymCampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        campaign = serializer.save(gym=gym)

        sent_count = email_service.send_campaign(gym, campaign)

        return Response({
            'message': f'Campaign sent to {sent_count} user(s) nearby.',
            'sent_to_count': sent_count,
            'campaign': GymCampaignListSerializer(campaign, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class GymCampaignListView(generics.ListAPIView):
    """GET /api/gyms/<id>/campaigns/ — list a gym's sent campaigns."""
    serializer_class = GymCampaignListSerializer

    def get_queryset(self):
        return GymEmailCampaign.objects.filter(
            gym_id=self.kwargs['pk'],
            sent_at__isnull=False,
        ).select_related('gym')


class UserCampaignInboxView(generics.ListAPIView):
    """
    GET /api/gyms/inbox/
    Authenticated user sees all campaigns from gyms they follow.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GymCampaignListSerializer

    def get_queryset(self):
        followed_ids = GymMembership.objects.filter(
            user=self.request.user
        ).values_list('gym_id', flat=True)
        return GymEmailCampaign.objects.filter(
            gym_id__in=followed_ids,
            sent_at__isnull=False,
        ).select_related('gym').order_by('-sent_at')
