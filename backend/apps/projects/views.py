from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import Membership
from apps.tasks.models import Task

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        org_slug = self.kwargs.get("org_slug")
        if org_slug:
            qs = Project.objects.filter(
                organization__slug=org_slug,
                organization__memberships__user=user,
            )
        else:
            org_slugs = Membership.objects.filter(user=user).values_list(
                "organization__slug", flat=True
            )
            qs = Project.objects.filter(organization__slug__in=org_slugs)

        qs = qs.select_related("organization", "created_by")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if not Membership.objects.filter(user=user, organization=obj.organization).exists():
            raise NotFound()
        return obj

    def perform_create(self, serializer):
        org_slug = self.kwargs.get("org_slug")
        if not org_slug:
            raise PermissionDenied("Organization context required.")
        membership = Membership.objects.filter(
            user=self.request.user, organization__slug=org_slug
        ).first()
        if not membership:
            raise NotFound()
        if membership.role not in (Membership.OWNER, Membership.ADMIN):
            raise PermissionDenied("Only OWNER or ADMIN can create projects.")
        serializer.save(
            organization_id=membership.organization_id,
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        obj = serializer.instance
        membership = Membership.objects.filter(
            user=self.request.user, organization=obj.organization
        ).first()
        if not membership or membership.role not in (Membership.OWNER, Membership.ADMIN):
            raise PermissionDenied("Only OWNER or ADMIN can update projects.")
        serializer.save()

    def perform_destroy(self, instance):
        membership = Membership.objects.filter(
            user=self.request.user, organization=instance.organization
        ).first()
        if not membership or membership.role not in (Membership.OWNER, Membership.ADMIN):
            raise PermissionDenied("Only OWNER or ADMIN can delete projects.")
        instance.delete()

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        project = self.get_object()
        from django.db.models import Count
        counts = (
            Task.objects.filter(project=project)
            .values("status")
            .annotate(count=Count("id"))
        )
        result = {choice[0]: 0 for choice in Task.STATUS_CHOICES}
        for row in counts:
            result[row["status"]] = row["count"]
        result["total"] = sum(result.values())
        return Response({
            "project_id": project.id,
            "project_name": project.name,
            "counts": result,
        })