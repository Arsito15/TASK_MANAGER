from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.organizations.models import Organization, Membership
from apps.projects.models import Project


class ProjectPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="StrongPass123!"
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@test.com", password="StrongPass123!"
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="StrongPass123!"
        )
        self.viewer = User.objects.create_user(
            username="viewer", email="viewer@test.com", password="StrongPass123!"
        )
        self.outsider = User.objects.create_user(
            username="outsider", email="outsider@test.com", password="StrongPass123!"
        )
        self.org = Organization.objects.create(name="Test Org", created_by=self.owner)
        Membership.objects.create(user=self.owner, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(user=self.admin, organization=self.org, role=Membership.ADMIN)
        Membership.objects.create(user=self.member, organization=self.org, role=Membership.MEMBER)
        Membership.objects.create(user=self.viewer, organization=self.org, role=Membership.VIEWER)

    def _url(self):
        return reverse("projects:project-list", kwargs={"org_slug": self.org.slug})

    def test_member_cannot_create_project(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.post(self._url(), {"name": "New Project"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_create_project(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post(self._url(), {"name": "New Project"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_project(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self._url(), {"name": "New Project"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_owner_can_create_project(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(self._url(), {"name": "New Project"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_outsider_cannot_list_projects(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("results", [])), 0)

    def test_outsider_cannot_access_project_detail(self):
        project = Project.objects.create(
            name="P1", organization=self.org, created_by=self.owner
        )
        self.client.force_authenticate(user=self.outsider)
        url = reverse("projects:project-detail", kwargs={"pk": project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_update_project(self):
        project = Project.objects.create(
            name="P1", organization=self.org, created_by=self.owner
        )
        self.client.force_authenticate(user=self.member)
        url = reverse("projects:project-detail", kwargs={"pk": project.id, "org_slug": self.org.slug})
        resp = self.client.patch(url, {"name": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_filter_by_status(self):
        Project.objects.create(name="Active", organization=self.org, created_by=self.owner)
        Project.objects.create(
            name="Archived", organization=self.org, created_by=self.owner, status=Project.ARCHIVED
        )
        self.client.force_authenticate(user=self.member)
        url = self._url() + "?status=ARCHIVED"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in resp.data.get("results", [])]
        self.assertEqual(names, ["Archived"])