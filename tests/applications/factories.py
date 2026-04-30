import factory
from django.contrib.auth.models import User
from django.utils import timezone

from applications.models import Application, Company, Contact, TimelineEvent


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")

    @classmethod
    def _after_postgeneration(
        cls, instance: User, create: bool, results: dict | None = None
    ) -> None:
        if create and results:
            instance.save()


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    website = "https://example.com"
    industry = "Tech"
    location = "Genève, CH"


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    user = factory.SubFactory(UserFactory)
    company = factory.SubFactory(CompanyFactory)
    position_title = factory.Sequence(lambda n: f"Développeur Full-Stack {n}")
    source = Application.Source.LINKEDIN
    status = Application.Status.SENT
    applied_at = factory.LazyFunction(timezone.now)
    last_activity_at = factory.LazyFunction(timezone.now)


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    application = factory.SubFactory(ApplicationFactory)
    name = factory.Sequence(lambda n: f"Contact {n}")
    role = "Recruteur"
    email = factory.Sequence(lambda n: f"contact{n}@example.com")


class TimelineEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimelineEvent

    application = factory.SubFactory(ApplicationFactory)
    event_type = TimelineEvent.EventType.NOTE
    occurred_at = factory.LazyFunction(timezone.now)
    description = "Test event"
