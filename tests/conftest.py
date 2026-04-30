import pytest
from django.contrib.auth.models import User
from django.test import Client

_BACKEND = "django.contrib.auth.backends.ModelBackend"


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


def force_login(client: Client, user: User) -> None:
    client.force_login(user, backend=_BACKEND)
