from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from applications.models import Application
from stats import services
from tests.applications.factories import ApplicationFactory, UserFactory
from tests.conftest import force_login


@pytest.mark.django_db
class TestSummaryService:
    def test_counts_total_active_overdue_this_week(self):
        user = UserFactory()
        ApplicationFactory(user=user, status=Application.Status.SENT)
        ApplicationFactory(user=user, status=Application.Status.REJECTED)
        ApplicationFactory(
            user=user,
            status=Application.Status.PHONE_SCREEN,
            next_action_date=timezone.now().date() - timedelta(days=1),
        )
        result = services.summary(user)
        assert result["total"] == 3
        assert result["active"] == 2
        assert result["overdue"] == 1

    def test_other_users_excluded(self):
        user = UserFactory()
        other = UserFactory()
        ApplicationFactory(user=other)
        ApplicationFactory(user=other)
        result = services.summary(user)
        assert result["total"] == 0


@pytest.mark.django_db
class TestPerStatusService:
    def test_returns_all_statuses_with_counts(self):
        user = UserFactory()
        ApplicationFactory(user=user, status=Application.Status.SENT)
        ApplicationFactory(user=user, status=Application.Status.SENT)
        ApplicationFactory(user=user, status=Application.Status.OFFER)

        result = services.per_status(user)
        sent = next(r for r in result if r["value"] == "sent")
        offer = next(r for r in result if r["value"] == "offer")
        draft = next(r for r in result if r["value"] == "draft")
        assert sent["count"] == 2
        assert offer["count"] == 1
        assert draft["count"] == 0


@pytest.mark.django_db
class TestPerSourceService:
    def test_returns_only_used_sources(self):
        user = UserFactory()
        ApplicationFactory(user=user, source=Application.Source.LINKEDIN)
        ApplicationFactory(user=user, source=Application.Source.LINKEDIN)
        result = services.per_source(user)
        assert len(result) == 1
        assert result[0]["value"] == "linkedin"
        assert result[0]["count"] == 2


@pytest.mark.django_db
class TestWeeklyService:
    def test_returns_n_weeks(self):
        user = UserFactory()
        result = services.weekly_volume(user, weeks=4)
        assert len(result) == 4
        assert all("week_start" in row and "count" in row for row in result)
        assert all(row["count"] == 0 for row in result)

    def test_counts_applications_in_their_week(self):
        user = UserFactory()
        ApplicationFactory(user=user)
        ApplicationFactory(user=user)
        result = services.weekly_volume(user, weeks=4)
        total = sum(row["count"] for row in result)
        assert total == 2


@pytest.mark.django_db
class TestFunnelService:
    def test_progression_is_cumulative(self):
        user = UserFactory()
        ApplicationFactory(user=user, status=Application.Status.SENT)
        ApplicationFactory(user=user, status=Application.Status.PHONE_SCREEN)
        ApplicationFactory(user=user, status=Application.Status.TECHNICAL)
        ApplicationFactory(user=user, status=Application.Status.OFFER)

        result = services.funnel(user)
        stages = {r["stage"]: r["count"] for r in result}
        assert stages["sent"] == 4
        assert stages["screen"] == 3
        assert stages["interview"] == 2
        assert stages["offer"] == 1

    def test_excludes_draft_and_withdrawn(self):
        user = UserFactory()
        ApplicationFactory(user=user, status=Application.Status.DRAFT)
        ApplicationFactory(user=user, status=Application.Status.WITHDRAWN)
        result = services.funnel(user)
        assert all(r["count"] == 0 for r in result)


@pytest.mark.django_db
class TestStatsEndpoints:
    @pytest.mark.parametrize(
        "name", ["summary", "per_status", "per_source", "weekly", "funnel"]
    )
    def test_endpoint_requires_auth(self, client, name):
        resp = client.get(reverse(f"stats:{name}"))
        assert resp.status_code in (401, 403)

    @pytest.mark.parametrize(
        "name", ["summary", "per_status", "per_source", "weekly", "funnel"]
    )
    def test_authenticated_returns_200(self, client, name):
        user = UserFactory()
        ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.get(reverse(f"stats:{name}"))
        assert resp.status_code == 200

    def test_summary_payload_shape(self, client):
        user = UserFactory()
        ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.get(reverse("stats:summary"))
        body = resp.json()
        assert set(body.keys()) == {"total", "active", "overdue", "this_week"}

    def test_isolation_between_users(self, client):
        user = UserFactory()
        other = UserFactory()
        ApplicationFactory(user=other)
        ApplicationFactory(user=other)
        force_login(client, user)
        resp = client.get(reverse("stats:summary"))
        assert resp.json()["total"] == 0

    def test_weekly_accepts_weeks_param(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.get(reverse("stats:weekly"), {"weeks": "4"})
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_weekly_clamps_invalid_param(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.get(reverse("stats:weekly"), {"weeks": "999"})
        assert resp.status_code == 200
        assert len(resp.json()) == 52


@pytest.mark.django_db
class TestStatsPage:
    def test_redirects_anonymous(self, client):
        resp = client.get(reverse("stats_page"))
        assert resp.status_code == 302

    def test_authenticated_renders(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.get(reverse("stats_page"))
        assert resp.status_code == 200
        assert b"Statistiques" in resp.content
