from django.urls import path

from . import views

app_name = "stats"

urlpatterns = [
    path("summary/", views.stats_summary, name="summary"),
    path("status/", views.stats_per_status, name="per_status"),
    path("source/", views.stats_per_source, name="per_source"),
    path("weekly/", views.stats_weekly, name="weekly"),
    path("funnel/", views.stats_funnel, name="funnel"),
]
