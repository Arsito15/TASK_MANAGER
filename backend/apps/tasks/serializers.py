from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.organizations.models import Membership
from .models import Task, ActivityLog

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    assignee_email = serializers.CharField(source="assignee.email", read_only=True)
    assignee_name = serializers.SerializerMethodField()
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_email",
            "assignee_name",
            "due_date",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project",
            "created_by",
            "created_by_email",
            "assignee_email",
            "assignee_name",
            "created_at",
            "updated_at",
        )

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.get_full_name() or obj.assignee.username
        return None

    def validate_assignee(self, value):
        if value is None:
            return value
        project = self.context.get("project")
        if project:
            if not Membership.objects.filter(
                user=value, organization=project.organization
            ).exists():
                raise serializers.ValidationError(
                    "Assignee must be a member of the project's organization."
                )
        return value


class TaskStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True, default="")

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "task",
            "task_title",
            "user",
            "user_email",
            "action",
            "detail",
            "created_at",
        )
        read_only_fields = fields