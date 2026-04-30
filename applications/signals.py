from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Application, TimelineEvent


@receiver(pre_save, sender=Application)
def create_status_change_event(
    sender: type[Application], instance: Application, **kwargs: object
) -> None:
    if not instance.pk:
        return

    try:
        previous = Application.objects.get(pk=instance.pk)
    except Application.DoesNotExist:
        return

    if previous.status != instance.status:
        TimelineEvent.objects.create(
            application=instance,
            event_type=TimelineEvent.EventType.STATUS_CHANGE,
            occurred_at=timezone.now(),
            description=(
                f"Statut changé de « {previous.get_status_display()} » "
                f"vers « {instance.get_status_display()} »"
            ),
        )
        instance.last_activity_at = timezone.now()
