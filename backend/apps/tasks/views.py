from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.organizations.models import Membership

from .models import Task, ActivityLog
from .serializers import TaskSerializer, TaskStatusChangeSerializer

User = get_user_model()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "priority", "assignee"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "due_date", "priority", "status"]

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get("project_id")

        if project_id:
            qs = Task.objects.filter(
                project_id=project_id,
                project__organization__memberships__user=user,
            )
        else:
            org_slugs = Membership.objects.filter(user=user).values_list(
                "organization__slug", flat=True
            )
            qs = Task.objects.filter(project__organization__slug__in=org_slugs)

        return qs.select_related(
            "assignee", "created_by", "project", "project__organization"
        )

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if not Membership.objects.filter(
            user=user, organization=obj.project.organization
        ).exists():
            raise NotFound()
        return obj

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        project_id = self.kwargs.get("project_id")
        if project_id:
            from apps.projects.models import Project
            try:
                ctx["project"] = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                pass
        return ctx

    def _get_membership(self, project):
        return Membership.objects.filter(
            user=self.request.user, organization=project.organization
        ).first()

    def _log(self, task, action, detail=""):
        ActivityLog.objects.create(
            task=task,
            project=task.project,
            user=self.request.user,
            action=action,
            detail=detail,
        )

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        if not project_id:
            raise PermissionDenied("Project context required.")
        from apps.projects.models import Project
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise NotFound()
        membership = self._get_membership(project)
        if not membership:
            raise NotFound()
        if membership.role == Membership.VIEWER:
            raise PermissionDenied("VIEWER users cannot create tasks.")
        task = serializer.save(project=project, created_by=self.request.user)
        self._log(task, ActivityLog.CREATED, f'"{task.title}"')

    def perform_update(self, serializer):
        task = serializer.instance
        membership = self._get_membership(task.project)
        if not membership:
            raise NotFound()
        is_creator = task.created_by_id == self.request.user.id
        is_admin = membership.role in (Membership.OWNER, Membership.ADMIN)
        if not (is_creator or is_admin):
            raise PermissionDenied(
                "Only the task creator or an ADMIN/OWNER can edit this task."
            )
        task = serializer.save()
        self._log(task, ActivityLog.UPDATED, f'"{task.title}"')

    def perform_destroy(self, instance):
        membership = self._get_membership(instance.project)
        if not membership:
            raise NotFound()
        is_creator = instance.created_by_id == self.request.user.id
        is_admin = membership.role in (Membership.OWNER, Membership.ADMIN)
        if not (is_creator or is_admin):
            raise PermissionDenied(
                "Only the task creator or an ADMIN/OWNER can delete this task."
            )
        self._log(instance, ActivityLog.DELETED, f'"{instance.title}"')
        instance.delete()

    @action(detail=True, methods=["patch"], url_path="change-status")
    def change_status(self, request, pk=None, project_id=None):
        task = self.get_object()
        serializer = TaskStatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = self._get_membership(task.project)
        if not membership:
            raise NotFound()
        is_creator = task.created_by_id == request.user.id
        is_assignee = task.assignee_id == request.user.id
        is_admin = membership.role in (Membership.OWNER, Membership.ADMIN)
        if not (is_creator or is_assignee or is_admin):
            raise PermissionDenied(
                "Only the task creator, assignee, or an ADMIN/OWNER can change the status."
            )
        old_status = task.status
        new_status = serializer.validated_data["status"]
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])
        self._log(
            task,
            ActivityLog.STATUS_CHANGED,
            f"{old_status} -> {new_status}",
        )
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data)