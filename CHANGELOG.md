# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Sprint 4 — Stats & Reminders
- DRF endpoints under `/api/v1/stats/` (summary, status, source, weekly, funnel)
- Stats page with Chart.js (doughnut, bar, line, funnel)
- `stats/` app with isolated services layer

### Sprint 3 — Timeline & Contacts
- Contacts CRUD with htmx (inline create / edit / delete)
- Timeline tab with manual event creation and deletion
- Markdown rendering for application notes (markdown2 in safe mode)

### Sprint 2 — Frontend CRUD
- Application list view with search and filters (status, source, query)
- Application create/edit form with company autocomplete (datalist)
- Application detail page with Alpine.js tabs (infos / notes / contacts / timeline)
- Inline status change widget (htmx GET/POST toggle)
- 60+ functional view tests

### Sprint 1 — Foundations
- Initial Django project structure with per-app layout (no `apps/` wrapper)
- Models: Company, Application, Contact, TimelineEvent
- Django admin with inlines and filters
- Signal: auto-create TimelineEvent on status change
- Auth via django-allauth (email login)
- Base templates with Tailwind CSS, htmx, Alpine.js
- Dashboard: active applications + follow-up alerts
- pytest suite with factory_boy factories
- Docker Compose setup (web + postgres)
- GitHub Actions CI (lint + tests)
