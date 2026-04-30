import pytest
from django.urls import reverse

from applications.models import Contact, TimelineEvent
from tests.conftest import force_login

from .factories import (
    ApplicationFactory,
    ContactFactory,
    TimelineEventFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestContactCreate:
    def test_redirects_anonymous(self, client):
        app = ApplicationFactory()
        resp = client.get(reverse("contact_create", kwargs={"pk": app.pk}))
        assert resp.status_code == 302

    def test_get_renders_form(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.get(reverse("contact_create", kwargs={"pk": app.pk}))
        assert resp.status_code == 200
        assert b"Nouveau contact" in resp.content

    def test_post_creates_contact_and_returns_list(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.post(
            reverse("contact_create", kwargs={"pk": app.pk}),
            {
                "name": "Alice Recruteur",
                "role": "RH",
                "email": "alice@example.com",
                "phone": "",
                "linkedin": "",
                "notes": "",
            },
        )
        assert resp.status_code == 200
        assert Contact.objects.filter(application=app, name="Alice Recruteur").exists()
        assert b"Alice Recruteur" in resp.content

    def test_invalid_post_renders_form_with_errors(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.post(
            reverse("contact_create", kwargs={"pk": app.pk}),
            {
                "name": "",
                "role": "",
                "email": "",
                "phone": "",
                "linkedin": "",
                "notes": "",
            },
        )
        assert resp.status_code == 200
        assert not Contact.objects.filter(application=app).exists()

    def test_other_user_gets_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        force_login(client, user)
        resp = client.get(reverse("contact_create", kwargs={"pk": app.pk}))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestContactUpdate:
    def test_owner_can_update(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        contact = ContactFactory(application=app, name="Old Name")
        force_login(client, user)
        resp = client.post(
            reverse("contact_update", kwargs={"pk": app.pk, "contact_pk": contact.pk}),
            {
                "name": "New Name",
                "role": contact.role,
                "email": contact.email,
                "phone": "",
                "linkedin": "",
                "notes": "",
            },
        )
        assert resp.status_code == 200
        contact.refresh_from_db()
        assert contact.name == "New Name"

    def test_other_user_gets_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        contact = ContactFactory(application=app)
        force_login(client, user)
        resp = client.get(
            reverse("contact_update", kwargs={"pk": app.pk, "contact_pk": contact.pk})
        )
        assert resp.status_code == 404

    def test_contact_belonging_to_other_app_404(self, client):
        user = UserFactory()
        app1 = ApplicationFactory(user=user)
        app2 = ApplicationFactory(user=user)
        contact = ContactFactory(application=app2)
        force_login(client, user)
        resp = client.get(
            reverse("contact_update", kwargs={"pk": app1.pk, "contact_pk": contact.pk})
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestContactDelete:
    def test_post_deletes_contact(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        contact = ContactFactory(application=app)
        force_login(client, user)
        resp = client.post(
            reverse("contact_delete", kwargs={"pk": app.pk, "contact_pk": contact.pk})
        )
        assert resp.status_code == 200
        assert not Contact.objects.filter(pk=contact.pk).exists()

    def test_other_user_cannot_delete(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        contact = ContactFactory(application=app)
        force_login(client, user)
        resp = client.post(
            reverse("contact_delete", kwargs={"pk": app.pk, "contact_pk": contact.pk})
        )
        assert resp.status_code == 404
        assert Contact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
class TestEventCreate:
    def test_post_creates_event_and_updates_last_activity(self, client):
        from django.utils import timezone

        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        when = timezone.now().replace(microsecond=0)
        resp = client.post(
            reverse("event_create", kwargs={"pk": app.pk}),
            {
                "event_type": TimelineEvent.EventType.CALL,
                "occurred_at": when.strftime("%Y-%m-%dT%H:%M"),
                "description": "Appel avec le recruteur",
            },
        )
        assert resp.status_code == 200
        event = TimelineEvent.objects.get(
            application=app, description="Appel avec le recruteur"
        )
        assert event.event_type == TimelineEvent.EventType.CALL
        app.refresh_from_db()
        assert app.last_activity_at == event.occurred_at

    def test_invalid_post_does_not_create(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        force_login(client, user)
        resp = client.post(
            reverse("event_create", kwargs={"pk": app.pk}),
            {"event_type": "", "occurred_at": "", "description": ""},
        )
        assert resp.status_code == 200
        # status_change events from factory creation may exist; user-created NOTEs should not
        assert not TimelineEvent.objects.filter(
            application=app, event_type=TimelineEvent.EventType.CALL
        ).exists()

    def test_other_user_404(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        force_login(client, user)
        resp = client.get(reverse("event_create", kwargs={"pk": app.pk}))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestEventDelete:
    def test_owner_can_delete(self, client):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        event = TimelineEventFactory(application=app)
        force_login(client, user)
        resp = client.post(
            reverse("event_delete", kwargs={"pk": app.pk, "event_pk": event.pk})
        )
        assert resp.status_code == 200
        assert not TimelineEvent.objects.filter(pk=event.pk).exists()

    def test_other_user_cannot_delete(self, client):
        user = UserFactory()
        other = UserFactory()
        app = ApplicationFactory(user=other)
        event = TimelineEventFactory(application=app)
        force_login(client, user)
        resp = client.post(
            reverse("event_delete", kwargs={"pk": app.pk, "event_pk": event.pk})
        )
        assert resp.status_code == 404
        assert TimelineEvent.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
class TestMarkdownFilter:
    def test_renders_markdown(self):
        from applications.templatetags.application_tags import markdown_filter

        html = markdown_filter("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_empty_input_returns_empty(self):
        from applications.templatetags.application_tags import markdown_filter

        assert markdown_filter("") == ""
        assert markdown_filter(None) == ""

    def test_escapes_raw_html(self):
        from applications.templatetags.application_tags import markdown_filter

        html = markdown_filter("<script>alert(1)</script>")
        assert "<script>" not in html
