import pytest
from django.urls import reverse

from applications.models import Application, TimelineEvent
from tests.conftest import force_login

from .factories import ApplicationFactory, UserFactory


@pytest.mark.django_db
class TestDashboard:
    def test_redirects_anonymous(self, client):
        resp = client.get(reverse("dashboard"))
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]

    def test_authenticated_user_sees_dashboard(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.get(reverse("dashboard"))
        assert resp.status_code == 200

    def test_only_own_applications_shown(self, client):
        user = UserFactory()
        other = UserFactory()
        ApplicationFactory(user=user, position_title="My Job")
        ApplicationFactory(user=other, position_title="Other Job")
        force_login(client, user)
        resp = client.get(reverse("dashboard"))
        assert resp.status_code == 200
        assert "My Job" in resp.content.decode()
        assert "Other Job" not in resp.content.decode()


@pytest.mark.django_db
class TestApplicationList:
    def test_redirects_anonymous(self, client):
        resp = client.get(reverse("application_list"))
        assert resp.status_code == 302

    def test_lists_own_applications(self, client):
        user = UserFactory()
        ApplicationFactory(user=user, position_title="Django Dev")
        force_login(client, user)
        resp = client.get(reverse("application_list"))
        assert resp.status_code == 200
        assert "Django Dev" in resp.content.decode()

    def test_filters_by_status(self, client):
        user = UserFactory()
        ApplicationFactory(
            user=user, position_title="Sent Job", status=Application.Status.SENT
        )
        ApplicationFactory(
            user=user, position_title="Draft Job", status=Application.Status.DRAFT
        )
        force_login(client, user)
        resp = client.get(
            reverse("application_list"), {"status": Application.Status.SENT}
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Sent Job" in content
        assert "Draft Job" not in content

    def test_filters_by_query(self, client):
        user = UserFactory()
        ApplicationFactory(user=user, position_title="Python Engineer")
        ApplicationFactory(user=user, position_title="Marketing Manager")
        force_login(client, user)
        resp = client.get(reverse("application_list"), {"q": "Python"})
        content = resp.content.decode()
        assert "Python Engineer" in content
        assert "Marketing Manager" not in content

    def test_does_not_show_other_users_applications(self, client):
        user = UserFactory()
        other = UserFactory()
        ApplicationFactory(user=other, position_title="Secret Job")
        force_login(client, user)
        resp = client.get(reverse("application_list"))
        assert "Secret Job" not in resp.content.decode()


@pytest.mark.django_db
class TestApplicationCreate:
    def test_redirects_anonymous(self, client):
        resp = client.get(reverse("application_create"))
        assert resp.status_code == 302

    def test_get_shows_form(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.get(reverse("application_create"))
        assert resp.status_code == 200

    def test_post_creates_application_and_redirects(self, client):
        user = UserFactory()
        force_login(client, user)
        resp = client.post(
            reverse("application_create"),
            {
                "company_name": "Startup SA",
                "position_title": "Lead Dev",
                "source": Application.Source.LINKEDIN,
                "status": Application.Status.SENT,
                "work_mode": Application.WorkMode.HYBRID,
                "currency": Application.Currency.CHF,
            },
        )
        assert resp.status_code == 302
        app = Application.objects.get(user=user, position_title="Lead Dev")
        assert app.company.name == "Startup SA"

    def test_post_reuses_existing_company(self, client):
        from applications.models import Company

        user = UserFactory()
        Company.objects.create(name="Existing Corp")
        force_login(client, user)
        client.post(
            reverse("application_create"),
            {
                "company_name": "Existing Corp",
                "position_title": "Dev",
                "source": Application.Source.DIRECT,
                "status": Application.Status.DRAFT,
                "work_mode": Application.WorkMode.ONSITE,
                "currency": Application.Currency.EUR,
            },
        )
        from applications.models import Company

        assert Company.objects.filter(name="Existing Corp").count() == 1


@pytest.mark.django_db
class TestApplicationDetail:
    def test_redirects_anonymous(self, client):
        app = ApplicationFactory()
        resp = client.get(reverse("application_detail", kwargs={"pk": app.pk}))
        assert resp.status_code == 302

    def test_owner_can_view(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user, position_title="Senior Dev")
        force_login(client, user)
        resp = client.get(reverse("application_detail", kwargs={"pk": app.pk}))
        assert resp.status_code == 200
        assert "Senior Dev" in resp.content.decode()

    def test_other_user_gets_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        force_login(client, user)
        resp = client.get(reverse("application_detail", kwargs={"pk": app.pk}))
        assert resp.status_code == 404

    def test_tabs_context_present(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.get(reverse("application_detail", kwargs={"pk": app.pk}))
        assert "tabs" in resp.context
        tab_keys = [t for t, _ in resp.context["tabs"]]
        assert "infos" in tab_keys
        assert "notes" in tab_keys
        assert "contacts" in tab_keys
        assert "timeline" in tab_keys


@pytest.mark.django_db
class TestApplicationUpdate:
    def test_redirects_anonymous(self, client):
        app = ApplicationFactory()
        resp = client.get(reverse("application_edit", kwargs={"pk": app.pk}))
        assert resp.status_code == 302

    def test_owner_can_edit(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user, position_title="Old Title")
        force_login(client, user)
        resp = client.post(
            reverse("application_edit", kwargs={"pk": app.pk}),
            {
                "company_name": app.company.name,
                "position_title": "New Title",
                "source": app.source,
                "status": app.status,
                "work_mode": app.work_mode,
                "currency": app.currency,
            },
        )
        assert resp.status_code == 302
        app.refresh_from_db()
        assert app.position_title == "New Title"

    def test_other_user_gets_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        force_login(client, user)
        resp = client.post(
            reverse("application_edit", kwargs={"pk": app.pk}),
            {"position_title": "Hacked"},
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestStatusUpdate:
    def test_get_returns_select_partial(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.get(reverse("application_status_update", kwargs={"pk": app.pk}))
        assert resp.status_code == 200
        assert b"select" in resp.content.lower()

    def test_post_updates_status(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user, status=Application.Status.SENT)
        force_login(client, user)
        resp = client.post(
            reverse("application_status_update", kwargs={"pk": app.pk}),
            {"status": Application.Status.PHONE_SCREEN},
        )
        assert resp.status_code == 200
        app.refresh_from_db()
        assert app.status == Application.Status.PHONE_SCREEN

    def test_post_creates_timeline_event(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user, status=Application.Status.SENT)
        force_login(client, user)
        client.post(
            reverse("application_status_update", kwargs={"pk": app.pk}),
            {"status": Application.Status.TECHNICAL},
        )
        assert TimelineEvent.objects.filter(
            application=app,
            event_type=TimelineEvent.EventType.STATUS_CHANGE,
        ).exists()

    def test_post_ignores_invalid_status(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user, status=Application.Status.SENT)
        force_login(client, user)
        client.post(
            reverse("application_status_update", kwargs={"pk": app.pk}),
            {"status": "invalid_status"},
        )
        app.refresh_from_db()
        assert app.status == Application.Status.SENT

    def test_other_user_gets_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other, status=Application.Status.SENT)
        force_login(client, user)
        resp = client.post(
            reverse("application_status_update", kwargs={"pk": app.pk}),
            {"status": Application.Status.PHONE_SCREEN},
        )
        assert resp.status_code == 404
