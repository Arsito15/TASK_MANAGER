from rest_framework import permissions

from apps.organizations.models import Organization, Membership


class IsOrganizationMember(permissions.BasePermission):
    """User must be a member of the organization (view + object level)."""

    def _get_org_slug(self, view):
        return view.kwargs.get("org_slug")

    def has_permission(self, request, view):
        org_slug = self._get_org_slug(view)
        if not org_slug:
            return True
        return Organization.objects.filter(
            slug=org_slug, memberships__user=request.user
        ).exists()

    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user, organization=org
        ).exists()


class IsOrganizationAdmin(permissions.BasePermission):
    """User must be OWNER or ADMIN of the organization (view + object level)."""

    def _get_org_slug(self, view):
        return view.kwargs.get("org_slug")

    def has_permission(self, request, view):
        org_slug = self._get_org_slug(view)
        if not org_slug:
            return True
        return Membership.objects.filter(
            user=request.user,
            organization__slug=org_slug,
            role__in=[Membership.OWNER, Membership.ADMIN],
        ).exists()

    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user, organization=org, role__in=[Membership.OWNER, Membership.ADMIN]
        ).exists()