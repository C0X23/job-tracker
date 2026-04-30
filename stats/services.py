from collections import OrderedDict
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone

from applications.models import Application


def per_status(user: User) -> list[dict]:
    counts = dict(
        Application.objects.filter(user=user)
        .values_list("status")
        .annotate(n=Count("id"))
        .values_list("status", "n")
    )
    return [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in Application.Status.choices
    ]


def per_source(user: User) -> list[dict]:
    counts = dict(
        Application.objects.filter(user=user)
        .values_list("source")
        .annotate(n=Count("id"))
        .values_list("source", "n")
    )
    return [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in Application.Source.choices
        if counts.get(value, 0) > 0
    ]


def weekly_volume(user: User, weeks: int = 12) -> list[dict]:
    today = timezone.now().date()
    start = today - timedelta(weeks=weeks - 1)
    start = start - timedelta(days=start.weekday())

    rows = (
        Application.objects.filter(user=user, created_at__date__gte=start)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(n=Count("id"))
        .order_by("week")
    )
    by_week: dict[date, int] = {row["week"].date(): row["n"] for row in rows}

    out: list[dict] = []
    cursor = start
    for _ in range(weeks):
        out.append({"week_start": cursor.isoformat(), "count": by_week.get(cursor, 0)})
        cursor = cursor + timedelta(weeks=1)
    return out


_FUNNEL_STAGES = OrderedDict(
    [
        ("sent", {Application.Status.SENT}),
        (
            "screen",
            {Application.Status.SEEN, Application.Status.PHONE_SCREEN},
        ),
        (
            "interview",
            {Application.Status.TECHNICAL, Application.Status.FINAL},
        ),
        ("offer", {Application.Status.OFFER, Application.Status.ACCEPTED}),
    ]
)

# Stages are cumulative: reaching "interview" implies passing "screen" and "sent".
_PROGRESSION = {
    "sent": {
        Application.Status.SENT,
        Application.Status.SEEN,
        Application.Status.PHONE_SCREEN,
        Application.Status.TECHNICAL,
        Application.Status.FINAL,
        Application.Status.OFFER,
        Application.Status.ACCEPTED,
        Application.Status.REJECTED,
        Application.Status.GHOSTED,
    },
    "screen": {
        Application.Status.SEEN,
        Application.Status.PHONE_SCREEN,
        Application.Status.TECHNICAL,
        Application.Status.FINAL,
        Application.Status.OFFER,
        Application.Status.ACCEPTED,
    },
    "interview": {
        Application.Status.TECHNICAL,
        Application.Status.FINAL,
        Application.Status.OFFER,
        Application.Status.ACCEPTED,
    },
    "offer": {
        Application.Status.OFFER,
        Application.Status.ACCEPTED,
    },
}

_FUNNEL_LABELS = {
    "sent": "Envoyée",
    "screen": "Pré-entretien",
    "interview": "Entretien",
    "offer": "Offre",
}


def funnel(user: User) -> list[dict]:
    apps = list(
        Application.objects.filter(user=user)
        .exclude(status=Application.Status.DRAFT)
        .exclude(status=Application.Status.WITHDRAWN)
        .values_list("status", flat=True)
    )
    return [
        {
            "stage": stage,
            "label": _FUNNEL_LABELS[stage],
            "count": sum(1 for s in apps if s in statuses),
        }
        for stage, statuses in _PROGRESSION.items()
    ]


def summary(user: User) -> dict:
    qs = Application.objects.filter(user=user)
    today = timezone.now().date()
    return {
        "total": qs.count(),
        "active": sum(1 for a in qs if a.is_active),
        "overdue": sum(1 for a in qs if a.needs_followup),
        "this_week": qs.filter(
            created_at__date__gte=today - timedelta(days=today.weekday())
        ).count(),
    }
