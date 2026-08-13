from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Organization, Membership
from .serializers import OrganizationSerializer, MembershipSerializer
from .permissions import IsOrganizationMember, IsOrganizationAdmin


class OrganizationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Organization.objects.filter(memberships__user=self.request.user)
            .distinct()
            .select_related("created_by")
        )

    def perform_update(self, serializer):
        org = self.get_object()
        if not Membership.objects.filter(
            user=self.request.user, organization=org, role__in=[Membership.OWNER, Membership.ADMIN]
        ).exists():
            raise PermissionDenied("Only OWNER or ADMIN can update the organization.")
        serializer.save()

    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class MembershipViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        org_slug = self.kwargs.get("org_slug")
        return (
            Membership.objects.filter(
                organization__slug=org_slug,
                organization__memberships__user=self.request.user,
            )
            .select_related("user")
            .distinct()
            .order_by("-joined_at")
        )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOrganizationAdmin()]
        return [IsAuthenticated(), IsOrganizationMember()]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        org_slug = self.kwargs.get("org_slug")
        if org_slug:
            try:
                ctx["organization"] = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                from rest_framework.exceptions import NotFound
                raise NotFound("Organization not found.")
        return ctx

    def perform_create(self, serializer):
        org = self.get_serializer_context()["organization"]
        if not Membership.objects.filter(
            user=self.request.user, organization=org, role__in=[Membership.OWNER, Membership.ADMIN]
        ).exists():
            raise PermissionDenied("Only OWNER or ADMIN can manage members.")
        serializer.save()

    def perform_update(self, serializer):
        membership = self.get_object()
        if membership.role == Membership.OWNER and serializer.validated_data.get("role") != Membership.OWNER:
            raise PermissionDenied("Cannot demote the OWNER.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.role == Membership.OWNER:
            owner_count = Membership.objects.filter(
                organization=instance.organization, role=Membership.OWNER
            ).count()
            if owner_count <= 1:
                raise PermissionDenied("Cannot remove the last OWNER.")
        instance.delete()