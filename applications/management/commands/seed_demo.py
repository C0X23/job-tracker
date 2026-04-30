"""Idempotent demo seeder.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --email demo@cmegret.com --password demo1234

Creates a demo user with a realistic spread of applications, contacts, and
timeline events so that visitors landing on the homepage can immediately see
what the app looks like populated.
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.models import Application, Company, Contact, TimelineEvent

COMPANIES = [
    ("Proton", "https://proton.me", "SaaS / Privacy", "Genève, CH"),
    ("Doctolib", "https://doctolib.fr", "Healthtech", "Paris, FR"),
    ("Liip", "https://liip.ch", "Agence digitale", "Lausanne, CH"),
    ("Swisscom", "https://swisscom.ch", "Télécoms", "Bern, CH"),
    ("Algolia", "https://algolia.com", "DevTools", "Paris, FR"),
    ("Nexthink", "https://nexthink.com", "DEX / SaaS", "Lausanne, CH"),
    ("Qonto", "https://qonto.com", "Fintech", "Paris, FR"),
    ("Ledger", "https://ledger.com", "Crypto / Hardware", "Paris, FR"),
    ("Bestmile", "https://bestmile.com", "Mobility SaaS", "Lausanne, CH"),
    ("Datadog", "https://datadoghq.com", "Observability", "Paris, FR"),
    ("Smallpdf", "https://smallpdf.com", "SaaS / Productivity", "Zürich, CH"),
    ("Sonar", "https://sonarsource.com", "DevTools", "Genève, CH"),
]

# (position_title, status, source, work_mode, days_ago, salary_min, salary_max,
#  currency, has_followup, notes_md)
APPLICATIONS = [
    (
        "Backend Engineer (Python)",
        Application.Status.PHONE_SCREEN,
        Application.Source.LINKEDIN,
        Application.WorkMode.HYBRID,
        2,
        110_000,
        135_000,
        Application.Currency.CHF,
        True,
        "**Stack** : Python 3.12, Django, PostgreSQL, gRPC.\n"
        "Pré-entretien RH avec **Camille** prévu jeudi 15h.\n\n"
        "- Ils ouvrent 3 postes Python\n- Bureau à 8 min à pied de Cornavin\n- Hybride 2 jours/semaine sur place",
    ),
    (
        "Senior Django Developer",
        Application.Status.TECHNICAL,
        Application.Source.SWISSDEVJOBS,
        Application.WorkMode.REMOTE,
        7,
        70_000,
        85_000,
        Application.Currency.EUR,
        False,
        "Test technique reçu : refacto d'un service Django + tests pytest.\n"
        "Délai : 5 jours, à rendre **lundi prochain**.",
    ),
    (
        "Full-stack Python Developer",
        Application.Status.OFFER,
        Application.Source.REFERRAL,
        Application.WorkMode.HYBRID,
        14,
        95_000,
        115_000,
        Application.Currency.CHF,
        True,
        "Offre reçue ! 105k CHF + 8% bonus + 4 semaines de congés.\n\n"
        "À comparer avec Algolia avant de répondre. Réponse attendue avant **vendredi**.",
    ),
    (
        "Software Engineer",
        Application.Status.SEEN,
        Application.Source.JOBUP,
        Application.WorkMode.ONSITE,
        4,
        100_000,
        120_000,
        Application.Currency.CHF,
        False,
        "Annonce vue, en attente de retour RH.",
    ),
    (
        "Backend Engineer",
        Application.Status.FINAL,
        Application.Source.WELCOME,
        Application.WorkMode.HYBRID,
        20,
        65_000,
        80_000,
        Application.Currency.EUR,
        True,
        "Entretien final avec le CTO **mercredi**.\n\n## À préparer\n- Cas d'usage indexation\n- Architecture event-driven",
    ),
    (
        "Python Backend Developer",
        Application.Status.SENT,
        Application.Source.LINKEDIN,
        Application.WorkMode.REMOTE,
        1,
        105_000,
        125_000,
        Application.Currency.CHF,
        False,
        "Candidature spontanée envoyée hier soir.",
    ),
    (
        "Backend Engineer (Senior)",
        Application.Status.REJECTED,
        Application.Source.HELLOWORK,
        Application.WorkMode.HYBRID,
        25,
        75_000,
        95_000,
        Application.Currency.EUR,
        False,
        "Refusé. Feedback : profil orienté API, eux cherchent du data engineering pur.",
    ),
    (
        "Senior Python Engineer",
        Application.Status.GHOSTED,
        Application.Source.INDEED,
        Application.WorkMode.REMOTE,
        45,
        80_000,
        100_000,
        Application.Currency.EUR,
        False,
        "Aucune réponse depuis 6 semaines. Probablement perdue.",
    ),
    (
        "Python Developer",
        Application.Status.TECHNICAL,
        Application.Source.LINKEDIN,
        Application.WorkMode.HYBRID,
        10,
        95_000,
        110_000,
        Application.Currency.CHF,
        True,
        "Test technique : design d'une API de notifications. ~4h estimé.",
    ),
    (
        "Software Engineer III",
        Application.Status.SENT,
        Application.Source.DIRECT,
        Application.WorkMode.HYBRID,
        3,
        75_000,
        95_000,
        Application.Currency.EUR,
        False,
        "",
    ),
    (
        "Backend Developer",
        Application.Status.DRAFT,
        Application.Source.LINKEDIN,
        Application.WorkMode.REMOTE,
        0,
        None,
        None,
        Application.Currency.EUR,
        False,
        "Brouillon. Finir la lettre de motivation avant d'envoyer.",
    ),
    (
        "Senior Backend Engineer",
        Application.Status.WITHDRAWN,
        Application.Source.SWISSDEVJOBS,
        Application.WorkMode.ONSITE,
        18,
        90_000,
        110_000,
        Application.Currency.CHF,
        False,
        "Retirée — process trop long et stack legacy (Python 2.7).",
    ),
]

CONTACTS_FOR = {
    "Backend Engineer (Python)": [
        (
            "Camille Roux",
            "Talent Acquisition",
            "camille.roux@proton.me",
            "+41 22 555 01 02",
        ),
    ],
    "Full-stack Python Developer": [
        ("Sébastien Linder", "Engineering Manager", "seb@liip.ch", "+41 21 555 88 12"),
        ("Marie Dupont", "RH", "marie.dupont@liip.ch", ""),
    ],
    "Backend Engineer": [
        ("Thomas Bernard", "CTO", "thomas@welcome.dev", ""),
    ],
}


class Command(BaseCommand):
    help = "Seed a demo user with realistic example data (idempotent)."

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument("--email", default="demo@cmegret.com")
        parser.add_argument("--password", default="demo1234")

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        email: str = options["email"]
        password: str = options["password"]

        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "is_active": True},
        )
        user.email = email
        user.set_password(password)
        user.save()

        # Wipe previous demo applications so the command is idempotent.
        Application.objects.filter(user=user).delete()

        companies: dict[str, Company] = {}
        for name, website, industry, location in COMPANIES:
            company, _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    "website": website,
                    "industry": industry,
                    "location": location,
                },
            )
            companies[name] = company

        now = timezone.now()
        rng = random.Random(42)
        company_names = list(companies.keys())

        for idx, app_data in enumerate(APPLICATIONS):
            (
                title,
                status,
                source,
                work_mode,
                days_ago,
                salary_min,
                salary_max,
                currency,
                has_followup,
                notes,
            ) = app_data

            company_name = company_names[idx % len(company_names)]
            applied_at = now - timedelta(days=days_ago, hours=rng.randint(0, 12))
            next_action = (
                (now + timedelta(days=rng.choice([-2, -1, 1, 3, 5]))).date()
                if has_followup
                else None
            )

            app = Application.objects.create(
                user=user,
                company=companies[company_name],
                position_title=title,
                status=status,
                source=source,
                work_mode=work_mode,
                applied_at=applied_at if status != Application.Status.DRAFT else None,
                last_activity_at=applied_at,
                next_action_date=next_action,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                location=companies[company_name].location,
                notes=notes,
            )

            # Attach contacts when relevant
            for contact_data in CONTACTS_FOR.get(title, []):
                name, role, contact_email, phone = contact_data
                Contact.objects.create(
                    application=app,
                    name=name,
                    role=role,
                    email=contact_email,
                    phone=phone,
                )

            # Timeline: applied event
            if status != Application.Status.DRAFT:
                TimelineEvent.objects.create(
                    application=app,
                    event_type=TimelineEvent.EventType.APPLIED,
                    occurred_at=applied_at,
                    description="Candidature envoyée.",
                )

            # Add stage-specific events
            if status in {
                Application.Status.PHONE_SCREEN,
                Application.Status.TECHNICAL,
                Application.Status.FINAL,
                Application.Status.OFFER,
                Application.Status.ACCEPTED,
            }:
                TimelineEvent.objects.create(
                    application=app,
                    event_type=TimelineEvent.EventType.EMAIL_RECEIVED,
                    occurred_at=applied_at + timedelta(days=2),
                    description="Réponse RH positive, créneau d'entretien proposé.",
                )

            if status in {Application.Status.TECHNICAL, Application.Status.FINAL}:
                TimelineEvent.objects.create(
                    application=app,
                    event_type=TimelineEvent.EventType.INTERVIEW,
                    occurred_at=applied_at + timedelta(days=5),
                    description="Pré-entretien RH (30 min) — bon contact, suite confirmée.",
                )

            if status == Application.Status.OFFER:
                TimelineEvent.objects.create(
                    application=app,
                    event_type=TimelineEvent.EventType.OFFER,
                    occurred_at=applied_at + timedelta(days=12),
                    description="Offre formelle reçue par mail.",
                )

            if status == Application.Status.REJECTED:
                TimelineEvent.objects.create(
                    application=app,
                    event_type=TimelineEvent.EventType.REJECTION,
                    occurred_at=applied_at + timedelta(days=8),
                    description="Refus reçu, feedback constructif obtenu.",
                )

        msg = (
            f"Demo {'created' if created else 'updated'}: "
            f"{user.email} (password: {password}), "
            f"{len(APPLICATIONS)} applications, "
            f"{Contact.objects.filter(application__user=user).count()} contacts, "
            f"{TimelineEvent.objects.filter(application__user=user).count()} events."
        )
        self.stdout.write(self.style.SUCCESS(msg))
