from rest_framework import permissions

from apps.organizations.models import Membership


class IsOrganizationMember(permissions.BasePermission):
    """Object-level: user must be a member of the organization."""

    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user, organization=org
        ).exists()


class IsOrganizationAdmin(permissions.BasePermission):
    """Object-level: user must be OWNER or ADMIN of the organization."""

    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user, organization=org, role__in=[Membership.OWNER, Membership.ADMIN]
        ).exists()