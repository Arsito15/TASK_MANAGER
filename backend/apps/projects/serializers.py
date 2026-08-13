from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "id",
            "organization",
            "name",
            "description",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "organization", "created_by", "created_at", "updated_at")