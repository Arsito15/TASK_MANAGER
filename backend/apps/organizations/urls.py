from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import OrganizationViewSet, MembershipViewSet

app_name = "organizations"

router = SimpleRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")

member_router = SimpleRouter()
member_router.register(r"members", MembershipViewSet, basename="membership")

urlpatterns = [
    path("", include(router.urls)),
    path("organizations/<slug:org_slug>/", include(member_router.urls)),
]