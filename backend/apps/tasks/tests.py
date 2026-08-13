from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.organizations.models import Organization, Membership
from apps.projects.models import Project
from apps.tasks.models import Task, ActivityLog


class TaskPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="StrongPass123!"
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
        self.non_member = User.objects.create_user(
            username="nonmember", email="nm@test.com", password="StrongPass123!"
        )
        self.org = Organization.objects.create(name="Test Org", created_by=self.owner)
        self.other_org = Organization.objects.create(name="Other Org", created_by=self.outsider)
        Membership.objects.create(user=self.owner, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(user=self.member, organization=self.org, role=Membership.MEMBER)
        Membership.objects.create(user=self.viewer, organization=self.org, role=Membership.VIEWER)
        Membership.objects.create(user=self.outsider, organization=self.other_org, role=Membership.OWNER)
        self.project = Project.objects.create(
            name="P1", organization=self.org, created_by=self.owner
        )

    def _url(self):
        return reverse("tasks:task-list", kwargs={"project_id": self.project.id})

    def _detail_url(self, task_id):
        return reverse("tasks:task-detail", kwargs={"project_id": self.project.id, "pk": task_id})

    def _status_url(self, task_id):
        return reverse(
            "tasks:task-change-status",
            kwargs={"project_id": self.project.id, "pk": task_id},
        )

    def test_member_can_create_task(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.post(self._url(), {"title": "New Task"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_create_task(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post(self._url(), {"title": "New Task"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_access_tasks(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("results", [])), 0)

    def test_outsider_cannot_access_task_detail(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.owner
        )
        self.client.force_authenticate(user=self.outsider)
        url = reverse("tasks:task-detail", kwargs={"pk": task.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_assign_task_to_non_org_member(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.post(
            self._url(),
            {"title": "T1", "assignee": self.non_member.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_can_edit_own_task(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.member
        )
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(self._detail_url(task.id), {"title": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_member_cannot_edit_others_task(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.owner
        )
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(self._detail_url(task.id), {"title": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_edit_any_task(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.member
        )
        self.client.force_authenticate(user=self.owner)
        resp = self.client.patch(self._detail_url(task.id), {"title": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_creator_can_change_status(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.member
        )
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(
            self._status_url(task.id), {"status": "DONE"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "DONE")

    def test_viewer_cannot_change_status(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.member
        )
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.patch(
            self._status_url(task.id), {"status": "DONE"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_assignee_can_change_status(self):
        task = Task.objects.create(
            title="T1", project=self.project, created_by=self.owner
        )
        task.assignee = self.member
        task.save()
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(
            self._status_url(task.id), {"status": "IN_PROGRESS"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class TaskFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user", email="user@test.com", password="StrongPass123!"
        )
        self.assignee = User.objects.create_user(
            username="assignee", email="assignee@test.com", password="StrongPass123!"
        )
        self.org = Organization.objects.create(name="Org", created_by=self.user)
        Membership.objects.create(user=self.user, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(
            user=self.assignee, organization=self.org, role=Membership.MEMBER
        )
        self.project = Project.objects.create(
            name="P1", organization=self.org, created_by=self.user
        )
        Task.objects.create(title="Task A", project=self.project, created_by=self.user, status=Task.TODO, priority=Task.LOW)
        Task.objects.create(title="Task B", project=self.project, created_by=self.user, status=Task.DONE, priority=Task.HIGH, assignee=self.assignee)
        Task.objects.create(title="Important Task", project=self.project, created_by=self.user, status=Task.IN_PROGRESS, priority=Task.MEDIUM)
        self.client.force_authenticate(user=self.user)

    def test_filter_by_status(self):
        url = reverse("tasks:task-list", kwargs={"project_id": self.project.id})
        resp = self.client.get(url + "?status=DONE")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["title"], "Task B")

    def test_filter_by_priority(self):
        url = reverse("tasks:task-list", kwargs={"project_id": self.project.id})
        resp = self.client.get(url + "?priority=HIGH")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_search_by_title(self):
        url = reverse("tasks:task-list", kwargs={"project_id": self.project.id})
        resp = self.client.get(url + "?search=Important")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["title"], "Important Task")

    def test_pagination(self):
        url = reverse("tasks:task-list", kwargs={"project_id": self.project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("results", resp.data)


class ActivityLogTest(TestCase):
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
        self.other_org = Organization.objects.create(name="Other Org", created_by=self.outsider)
        Membership.objects.create(user=self.owner, organization=self.org, role=Membership.OWNER)
        Membership.objects.create(user=self.member, organization=self.org, role=Membership.MEMBER)
        Membership.objects.create(user=self.outsider, organization=self.other_org, role=Membership.OWNER)
        self.project = Project.objects.create(
            name="P1", organization=self.org, created_by=self.owner
        )

    def _url(self):
        return reverse("tasks:task-list", kwargs={"project_id": self.project.id})

    def _detail_url(self, task_id):
        return reverse("tasks:task-detail", kwargs={"project_id": self.project.id, "pk": task_id})

    def _status_url(self, task_id):
        return reverse(
            "tasks:task-change-status",
            kwargs={"project_id": self.project.id, "pk": task_id},
        )

    def _activity_url(self):
        return reverse("projects:project-activity", kwargs={"pk": self.project.id})

    def test_create_task_logs_activity(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.post(self._url(), {"title": "New Task"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        log = ActivityLog.objects.get(action=ActivityLog.CREATED)
        self.assertEqual(log.user, self.member)
        self.assertEqual(log.task_id, resp.data["id"])
        self.assertIn("New Task", log.detail)

    def test_update_task_logs_activity(self):
        task = Task.objects.create(title="T1", project=self.project, created_by=self.member)
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(self._detail_url(task.id), {"title": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        log = ActivityLog.objects.get(action=ActivityLog.UPDATED)
        self.assertEqual(log.user, self.member)
        self.assertIn("Updated", log.detail)

    def test_status_change_logs_activity(self):
        task = Task.objects.create(title="T1", project=self.project, created_by=self.member)
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(self._status_url(task.id), {"status": "DONE"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        log = ActivityLog.objects.get(action=ActivityLog.STATUS_CHANGED)
        self.assertEqual(log.user, self.member)
        self.assertIn("TODO -> DONE", log.detail)

    def test_delete_task_logs_activity(self):
        task = Task.objects.create(title="T1", project=self.project, created_by=self.member)
        self.client.force_authenticate(user=self.member)
        resp = self.client.delete(self._detail_url(task.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        log = ActivityLog.objects.get(action=ActivityLog.DELETED)
        self.assertEqual(log.user, self.member)
        self.assertIn("T1", log.detail)
        self.assertIsNone(log.task)

    def test_member_can_list_project_activity(self):
        task = Task.objects.create(title="T1", project=self.project, created_by=self.owner)
        ActivityLog.objects.create(
            task=task, project=self.project, user=self.owner,
            action=ActivityLog.CREATED, detail='"T1"',
        )
        self.client.force_authenticate(user=self.member)
        resp = self.client.get(self._activity_url())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["action"], "CREATED")
        self.assertEqual(resp.data["results"][0]["user_email"], "owner@test.com")

    def test_outsider_cannot_list_project_activity(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get(self._activity_url())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)