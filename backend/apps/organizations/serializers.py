from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Organization, Membership

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "created_by", "created_at", "my_role")
        read_only_fields = ("id", "slug", "created_by", "created_at", "my_role")

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        org = Organization.objects.create(created_by=request.user, **validated_data)
        Membership.objects.create(
            user=request.user, organization=org, role=Membership.OWNER
        )
        return org


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(write_only=True, required=False)
    user = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user", "username", "role", "joined_at", "user_email")
        read_only_fields = ("id", "user", "username", "joined_at")

    def validate_user_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        org = self.context["organization"]

        if self.instance:
            return attrs

        user_email = attrs.get("user_email")
        if not user_email:
            raise serializers.ValidationError({"user_email": "This field is required."})

        user = User.objects.filter(email__iexact=user_email).first()
        if Membership.objects.filter(user=user, organization=org).exists():
            raise serializers.ValidationError("User is already a member of this organization.")

        attrs["_user"] = user
        return attrs

    def create(self, validated_data):
        org = self.context["organization"]
        user = validated_data.pop("_user")
        validated_data.pop("user_email", None)
        return Membership.objects.create(user=user, organization=org, **validated_data)