import datetime

import pytest
from django.utils import timezone

from applications.models import Application, TimelineEvent

from .factories import ApplicationFactory, CompanyFactory, TimelineEventFactory


@pytest.mark.django_db
class TestCompany:
    def test_str(self) -> None:
        company = CompanyFactory(name="Acme Corp")
        assert str(company) == "Acme Corp"

    def test_name_is_unique(self) -> None:
        CompanyFactory(name="Unique Corp")
        with pytest.raises(Exception):
            CompanyFactory(name="Unique Corp")


@pytest.mark.django_db
class TestApplicationStrAndMeta:
    def test_str(self) -> None:
        app = ApplicationFactory(position_title="Dev Backend")
        assert "Dev Backend" in str(app)
        assert app.company.name in str(app)

    def test_ordering_by_last_activity(self) -> None:
        old = ApplicationFactory(
            last_activity_at=timezone.now() - datetime.timedelta(days=5)
        )
        recent = ApplicationFactory(last_activity_at=timezone.now())
        qs = Application.objects.filter(pk__in=[old.pk, recent.pk])
        assert qs[0].pk == recent.pk


@pytest.mark.django_db
class TestApplicationIsActive:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (Application.Status.DRAFT, True),
            (Application.Status.SENT, True),
            (Application.Status.SEEN, True),
            (Application.Status.PHONE_SCREEN, True),
            (Application.Status.TECHNICAL, True),
            (Application.Status.FINAL, True),
            (Application.Status.OFFER, True),
            (Application.Status.ACCEPTED, False),
            (Application.Status.REJECTED, False),
            (Application.Status.GHOSTED, False),
            (Application.Status.WITHDRAWN, False),
        ],
    )
    def test_is_active(self, status: str, expected: bool) -> None:
        app = ApplicationFactory(status=status)
        assert app.is_active is expected

    def test_all_statuses_covered(self) -> None:
        terminal = Application.TERMINAL_STATUSES
        all_statuses = {s.value for s in Application.Status}
        active_statuses = all_statuses - terminal
        assert len(terminal) + len(active_statuses) == len(all_statuses)


@pytest.mark.django_db
class TestApplicationNeedsFollowup:
    def test_no_date_returns_false(self) -> None:
        app = ApplicationFactory(next_action_date=None)
        assert app.needs_followup is False

    def test_future_date_returns_false(self) -> None:
        future = (timezone.now() + datetime.timedelta(days=3)).date()
        app = ApplicationFactory(
            next_action_date=future, status=Application.Status.SENT
        )
        assert app.needs_followup is False

    def test_past_date_returns_true(self) -> None:
        past = (timezone.now() - datetime.timedelta(days=2)).date()
        app = ApplicationFactory(next_action_date=past, status=Application.Status.SENT)
        assert app.needs_followup is True

    def test_today_returns_true(self) -> None:
        today = timezone.now().date()
        app = ApplicationFactory(next_action_date=today, status=Application.Status.SENT)
        assert app.needs_followup is True

    def test_terminal_status_returns_false_even_with_past_date(self) -> None:
        past = (timezone.now() - datetime.timedelta(days=2)).date()
        app = ApplicationFactory(
            next_action_date=past,
            status=Application.Status.REJECTED,
        )
        assert app.needs_followup is False


@pytest.mark.django_db
class TestStatusChangeSignal:
    def test_signal_creates_timeline_event_on_status_change(self) -> None:
        app = ApplicationFactory(status=Application.Status.SENT)
        initial_count = TimelineEvent.objects.filter(application=app).count()

        app.status = Application.Status.PHONE_SCREEN
        app.save()

        assert (
            TimelineEvent.objects.filter(application=app).count() == initial_count + 1
        )
        event = TimelineEvent.objects.filter(
            application=app,
            event_type=TimelineEvent.EventType.STATUS_CHANGE,
        ).latest("occurred_at")
        assert "Pré-entretien RH" in event.description

    def test_signal_does_not_fire_when_status_unchanged(self) -> None:
        app = ApplicationFactory(status=Application.Status.SENT)
        initial_count = TimelineEvent.objects.filter(application=app).count()

        app.position_title = "Updated Title"
        app.save()

        assert TimelineEvent.objects.filter(application=app).count() == initial_count

    def test_signal_updates_last_activity_on_status_change(self) -> None:
        old_time = timezone.now() - datetime.timedelta(hours=5)
        app = ApplicationFactory(
            status=Application.Status.SENT, last_activity_at=old_time
        )

        app.status = Application.Status.TECHNICAL
        app.save()
        app.refresh_from_db()

        assert app.last_activity_at > old_time


@pytest.mark.django_db
class TestTimelineEvent:
    def test_str(self) -> None:
        event = TimelineEventFactory(event_type=TimelineEvent.EventType.NOTE)
        assert "Note" in str(event)

    def test_ordering_most_recent_first(self) -> None:
        app = ApplicationFactory()
        old_event = TimelineEventFactory(
            application=app,
            occurred_at=timezone.now() - datetime.timedelta(days=1),
        )
        recent_event = TimelineEventFactory(
            application=app,
            occurred_at=timezone.now(),
        )
        events = list(TimelineEvent.objects.filter(application=app))
        assert events[0].pk == recent_event.pk
        assert events[1].pk == old_event.pk
