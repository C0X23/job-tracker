from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

from applications.views import (
    ApplicationCreateView,
    ApplicationDetailView,
    ApplicationListView,
    ApplicationUpdateView,
    application_status_update,
    contact_create,
    contact_delete,
    contact_update,
    dashboard,
    event_create,
    event_delete,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include("applications.urls")),
    path("api/v1/stats/", include("stats.urls")),
    path(
        "stats/",
        login_required(TemplateView.as_view(template_name="stats/stats.html")),
        name="stats_page",
    ),
    # Dashboard
    path("", dashboard, name="dashboard"),
    # Applications CRUD
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path(
        "applications/new/", ApplicationCreateView.as_view(), name="application_create"
    ),
    path(
        "applications/<int:pk>/",
        ApplicationDetailView.as_view(),
        name="application_detail",
    ),
    path(
        "applications/<int:pk>/edit/",
        ApplicationUpdateView.as_view(),
        name="application_edit",
    ),
    path(
        "applications/<int:pk>/status/",
        application_status_update,
        name="application_status_update",
    ),
    # Contacts (htmx)
    path(
        "applications/<int:pk>/contacts/new/",
        contact_create,
        name="contact_create",
    ),
    path(
        "applications/<int:pk>/contacts/<int:contact_pk>/edit/",
        contact_update,
        name="contact_update",
    ),
    path(
        "applications/<int:pk>/contacts/<int:contact_pk>/delete/",
        contact_delete,
        name="contact_delete",
    ),
    # Timeline events (htmx)
    path(
        "applications/<int:pk>/events/new/",
        event_create,
        name="event_create",
    ),
    path(
        "applications/<int:pk>/events/<int:event_pk>/delete/",
        event_delete,
        name="event_delete",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
