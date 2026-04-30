from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        SENT = "sent", "Envoyée"
        SEEN = "seen", "Vue / accusée"
        PHONE_SCREEN = "phone_screen", "Pré-entretien RH"
        TECHNICAL = "technical", "Entretien technique"
        FINAL = "final", "Entretien final"
        OFFER = "offer", "Offre reçue"
        ACCEPTED = "accepted", "Acceptée"
        REJECTED = "rejected", "Refusée"
        GHOSTED = "ghosted", "Sans réponse"
        WITHDRAWN = "withdrawn", "Retirée"

    class Source(models.TextChoices):
        LINKEDIN = "linkedin", "LinkedIn"
        INDEED = "indeed", "Indeed"
        JOBUP = "jobup", "Jobup.ch"
        SWISSDEVJOBS = "swissdevjobs", "SwissDevJobs"
        WELCOME = "welcome", "Welcome to the Jungle"
        HELLOWORK = "hellowork", "HelloWork"
        FREEWORK = "freework", "Free-Work"
        REFERRAL = "referral", "Cooptation"
        DIRECT = "direct", "Site carrière direct"
        HEADHUNTER = "headhunter", "Chasseur de tête"
        SPONTANEOUS = "spontaneous", "Spontanée"
        OTHER = "other", "Autre"

    class WorkMode(models.TextChoices):
        ONSITE = "onsite", "Présentiel"
        HYBRID = "hybrid", "Hybride"
        REMOTE = "remote", "Full remote"

    class Currency(models.TextChoices):
        EUR = "EUR", "€"
        CHF = "CHF", "CHF"

    TERMINAL_STATUSES = {
        Status.REJECTED,
        Status.GHOSTED,
        Status.WITHDRAWN,
        Status.ACCEPTED,
    }

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="applications"
    )

    position_title = models.CharField(max_length=200)
    job_url = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    work_mode = models.CharField(
        max_length=20, choices=WorkMode.choices, default=WorkMode.ONSITE
    )

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.EUR
    )

    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.LINKEDIN
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    applied_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    next_action_date = models.DateField(null=True, blank=True)

    cv_file = models.FileField(upload_to="cvs/%Y/%m/", blank=True)
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_activity_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "next_action_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.position_title} @ {self.company.name}"

    @property
    def is_active(self) -> bool:
        return self.status not in self.TERMINAL_STATUSES

    @property
    def needs_followup(self) -> bool:
        if not self.next_action_date or not self.is_active:
            return False
        return self.next_action_date <= timezone.now().date()


class Contact(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="contacts"
    )
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    linkedin = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.application})"


class TimelineEvent(models.Model):
    class EventType(models.TextChoices):
        APPLIED = "applied", "Candidature envoyée"
        EMAIL_SENT = "email_sent", "Email envoyé"
        EMAIL_RECEIVED = "email_received", "Email reçu"
        CALL = "call", "Appel téléphonique"
        INTERVIEW = "interview", "Entretien"
        TECHNICAL_TEST = "technical_test", "Test technique"
        OFFER = "offer", "Offre reçue"
        REJECTION = "rejection", "Refus reçu"
        STATUS_CHANGE = "status_change", "Changement de statut"
        NOTE = "note", "Note"

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    occurred_at = models.DateTimeField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} — {self.application}"
