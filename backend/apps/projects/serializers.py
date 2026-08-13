from rest_framework import serializers

from apps.organizations.models import Membership

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)
    my_role = serializers.SerializerMethodField()

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
            "my_role",
        )
        read_only_fields = (
            "id",
            "organization",
            "organization_slug",
            "created_by",
            "created_at",
            "updated_at",
            "my_role",
        )

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.organization.memberships.filter(user=request.user).first()
        return membership.role if membership else None