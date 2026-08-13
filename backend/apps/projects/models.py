from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class Project(models.Model):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (ARCHIVED, "Archived"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name