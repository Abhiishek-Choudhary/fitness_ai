"""Group service — owns all community-group business logic."""
from django.db.models import F, QuerySet

from community.models import CommunityGroup, GroupMember


# ── Queries ────────────────────────────────────────────────────────────────────

def get_groups(activity_focus: str = None, city: str = None,
                search: str = None) -> QuerySet:
    qs = CommunityGroup.objects.select_related('creator')
    if activity_focus:
        qs = qs.filter(activity_focus=activity_focus)
    if city:
        qs = qs.filter(city__icontains=city)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(description__icontains=search)
    return qs.order_by('-members_count')


def get_user_groups(user) -> QuerySet:
    member_group_ids = GroupMember.objects.filter(
        user=user, status='active'
    ).values_list('group_id', flat=True)
    return CommunityGroup.objects.filter(id__in=member_group_ids)


def get_membership(group: CommunityGroup, user) -> GroupMember | None:
    return GroupMember.objects.filter(group=group, user=user).first()


# ── Mutations ──────────────────────────────────────────────────────────────────

def create_group(creator, validated_data: dict) -> CommunityGroup:
    group = CommunityGroup.objects.create(creator=creator, **validated_data)
    GroupMember.objects.create(group=group, user=creator, role='admin', status='active')
    CommunityGroup.objects.filter(pk=group.pk).update(members_count=1)
    return group


def join_group(group: CommunityGroup, user) -> dict:
    existing = GroupMember.objects.filter(group=group, user=user).first()

    if existing:
        if existing.status == 'active':
            # Leave
            existing.delete()
            CommunityGroup.objects.filter(pk=group.pk).update(
                members_count=F('members_count') - 1
            )
            return {'action': 'left', 'status': None}
        if existing.status == 'pending':
            existing.delete()
            return {'action': 'request_withdrawn', 'status': None}
        if existing.status == 'banned':
            raise PermissionError("You have been banned from this group.")

    if group.privacy == 'public':
        GroupMember.objects.create(group=group, user=user, role='member', status='active')
        CommunityGroup.objects.filter(pk=group.pk).update(members_count=F('members_count') + 1)
        return {'action': 'joined', 'status': 'active'}
    else:
        GroupMember.objects.create(group=group, user=user, role='member', status='pending')
        return {'action': 'requested', 'status': 'pending'}


def approve_member(group: CommunityGroup, admin_user, target_user) -> GroupMember:
    admin_membership = GroupMember.objects.filter(
        group=group, user=admin_user, role='admin', status='active'
    ).first()
    if not admin_membership:
        raise PermissionError("Only group admins can approve members.")

    member = GroupMember.objects.filter(
        group=group, user=target_user, status='pending'
    ).first()
    if not member:
        raise ValueError("No pending request from this user.")

    member.status = 'active'
    member.save(update_fields=['status'])
    CommunityGroup.objects.filter(pk=group.pk).update(members_count=F('members_count') + 1)
    return member


def remove_member(group: CommunityGroup, admin_user, target_user) -> None:
    admin_membership = GroupMember.objects.filter(
        group=group, user=admin_user, role='admin', status='active'
    ).first()
    if not admin_membership:
        raise PermissionError("Only group admins can remove members.")
    if admin_user == target_user:
        raise ValueError("Cannot remove yourself as admin.")

    member = GroupMember.objects.filter(group=group, user=target_user, status='active').first()
    if not member:
        raise ValueError("User is not an active member.")

    member.delete()
    CommunityGroup.objects.filter(pk=group.pk).update(
        members_count=F('members_count') - 1
    )
