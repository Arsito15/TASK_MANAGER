from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.organizations.models import Organization, Membership


class OrganizationPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="StrongPass123!"
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="StrongPass123!"
        )
        self.outsider = User.objects.create_user(
            username="outsider", email="outsider@test.com", password="StrongPass123!"
        )
        self.org = Organization.objects.create(name="Test Org", created_by=self.owner)
        Membership.objects.create(user=self.owner, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(user=self.member, organization=self.org, role=Membership.MEMBER)
        self.client.force_authenticate(user=self.owner)

    def test_list_only_my_organizations(self):
        other_org = Organization.objects.create(name="Other Org", created_by=self.outsider)
        Membership.objects.create(user=self.outsider, organization=other_org, role=Membership.OWNER)
        self.client.force_authenticate(user=self.member)
        url = reverse("organizations:organization-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        org_names = [o["name"] for o in resp.data.get("results", resp.data)]
        self.assertIn("Test Org", org_names)
        self.assertNotIn("Other Org", org_names)

    def test_outsider_cannot_see_org_detail(self):
        self.client.force_authenticate(user=self.outsider)
        url = reverse("organizations:organization-detail", kwargs={"slug": self.org.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_update_org(self):
        self.client.force_authenticate(user=self.member)
        url = reverse("organizations:organization-detail", kwargs={"slug": self.org.slug})
        resp = self.client.patch(url, {"name": "Updated Org"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_org(self):
        url = reverse("organizations:organization-detail", kwargs={"slug": self.org.slug})
        resp = self.client.patch(url, {"name": "Updated Org"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_org_auto_creates_owner_membership(self):
        self.client.force_authenticate(user=self.outsider)
        url = reverse("organizations:organization-list")
        resp = self.client.post(url, {"name": "New Org"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_org = Organization.objects.get(name="New Org")
        membership = Membership.objects.get(user=self.outsider, organization=new_org)
        self.assertEqual(membership.role, Membership.OWNER)


class MembershipPermissionTest(TestCase):
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
        self.new_user = User.objects.create_user(
            username="newuser", email="new@test.com", password="StrongPass123!"
        )
        self.org = Organization.objects.create(name="Test Org", created_by=self.owner)
        Membership.objects.create(user=self.owner, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(user=self.admin, organization=self.org, role=Membership.ADMIN)
        Membership.objects.create(user=self.member, organization=self.org, role=Membership.MEMBER)

    def _members_url(self):
        return reverse("organizations:membership-list", kwargs={"org_slug": self.org.slug})

    def test_member_cannot_add_members(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.post(
            self._members_url(),
            {"user_email": "new@test.com", "role": "MEMBER"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_add_member(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self._members_url(),
            {"user_email": "new@test.com", "role": "MEMBER"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_add_nonexistent_user_fails(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self._members_url(),
            {"user_email": "nobody@test.com", "role": "MEMBER"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_demote_owner(self):
        membership = Membership.objects.get(user=self.owner, organization=self.org)
        url = reverse(
            "organizations:membership-detail",
            kwargs={"org_slug": self.org.slug, "pk": membership.id},
        )
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(url, {"role": "MEMBER"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_remove_last_owner(self):
        membership = Membership.objects.get(user=self.owner, organization=self.org)
        url = reverse(
            "organizations:membership-detail",
            kwargs={"org_slug": self.org.slug, "pk": membership.id},
        )
        self.client.force_authenticate(user=self.owner)
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)