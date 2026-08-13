from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "organization",
            "organization_slug",
            "name",
            "description",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization",
            "organization_slug",
            "created_by",
            "created_at",
            "updated_at",
        )