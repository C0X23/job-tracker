# Job Tracker

> Outil personnel de suivi de candidatures, construit avec Django.
> **[Démo live →](https://job-tracker.cmegret.com)** · `demo@cmegret.com` / `demo1234`

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![CI](https://github.com/C0X23/job-tracker/actions/workflows/ci.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-92%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

<!-- Replace with your own GIF / screenshots -->
<!-- ![Job Tracker demo](docs/screenshots/demo.gif) -->

---

## Why I built this

I built this while job-hunting myself. Tired of spreadsheets, I wanted a real tool to track my pipeline:
companies, contacts, timeline, follow-up alerts, conversion stats. The codebase is what I'd write at work,
not a tutorial demo — same architecture, same testing standards, same deployment hygiene.

It's now in production at [job-tracker.cmegret.com](https://job-tracker.cmegret.com), where I track my
own applications daily. The demo account is reset every 24 hours so visitors always see a populated app.

## Features

- **Applications** — full CRUD with status, source, salary range, work mode (onsite / hybrid / remote),
  CV upload, cover letter, free-form notes in Markdown
- **Contacts** — recruiters / managers attached to each application, inline create/edit/delete via htmx
- **Timeline** — manual events plus auto-tracked status changes (signal-driven)
- **Dashboard** — KPIs (active, overdue, weekly interviews, response rate), follow-up reminders, mini-funnel
- **Stats** — DRF endpoints + Chart.js views: per status, per source, weekly volume, conversion funnel
- **API REST** — authenticated session-based JSON API under `/api/v1/stats/`
- **No-reload UX** — htmx for inline mutations, Alpine.js for tab switching and toasts

## Stack

| Layer | Tech |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL 16 |
| Frontend | Django templates + htmx + Alpine.js + Tailwind CSS (custom mono-green theme, Inter Tight + JetBrains Mono) |
| Auth | django-allauth (email-only login) |
| Markdown | markdown2 (safe mode, HTML escaped) |
| Containerization | Docker Compose (dev + prod overrides) |
| Reverse proxy | Caddy 2 (automatic Let's Encrypt TLS) |
| CI/CD | GitHub Actions (lint, type-check, test, deploy via SSH) |
| Hosting | IONOS VPS (Ubuntu 24.04) |
| Tests | pytest-django + factory_boy, **92 tests, 97% coverage** |
| Quality | ruff, black, mypy strict |
| Backups | Daily `pg_dump` with 14-day retention |

## Design decisions

A few choices that aren't the obvious default and why I made them:

- **htmx instead of React.** Most actions are CRUD-with-feedback, not complex client state. htmx ships
  zero JS to the user (the library is 14 kB), no build step, no hydration. Alpine.js handles the few
  interactive bits (tabs, toasts). Pageloads are fast and the server stays the source of truth.
- **Caddy over Nginx.** Automatic HTTPS in 5 lines of config — no certbot cron jobs, no manual cert
  renewal. The Caddyfile is shorter than an Nginx server block doing the same thing.
- **Tailwind via CDN.** Solo project; the cost of a Node toolchain isn't justified. In a team setup
  I'd compile it for production.
- **Sessions over JWT for the API.** Same-origin only, browser client only. Sessions are simpler,
  more secure (httpOnly cookie), and ship less code.
- **One Django app per bounded context** (`applications`, `accounts`, `stats`) instead of an `apps/`
  wrapper. Standard Django, less magic.
- **Tests organised by app, not by type.** `tests/applications/test_views.py` is easier to navigate
  than a flat `tests/test_views.py` once the app grows.

## Running locally

```bash
git clone https://github.com/C0X23/job-tracker.git
cd job-tracker
cp .env.example .env
docker compose up --build
```

In a second terminal:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo  # optional: load 12 example applications
```

Open [http://localhost:8000](http://localhost:8000).

## Project structure

```
applications/      # Applications, contacts, timeline (models, views, htmx, signals)
accounts/          # allauth wrapper + login template
stats/             # DRF aggregation endpoints + Chart.js page

config/            # settings (base / dev / prod), urls, wsgi
templates/         # base.html (per-app templates live in each app/templates/)
static/            # Project-level static files (favicons)
tests/             # pytest, one folder per app
docker/            # Dockerfile + Caddyfile
scripts/           # Utility scripts (favicon generator)
```

## Tests

```bash
docker compose exec web pytest --cov=applications --cov=stats --cov=accounts
ruff check .
black --check .
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/v1/stats/summary/` | Total / active / overdue / this week |
| `GET /api/v1/stats/status/` | Distribution by status |
| `GET /api/v1/stats/source/` | Distribution by source (only used sources) |
| `GET /api/v1/stats/weekly/?weeks=12` | Volume per ISO week (1–52) |
| `GET /api/v1/stats/funnel/` | Cumulative conversion funnel |

Session authentication — the web pages and the API share the same session cookie.

## Deployment

Single-node Docker Compose on a VPS. Caddy terminates TLS and serves static files;
gunicorn serves Django; PostgreSQL runs in a sibling container; a backup container
runs `pg_dump` daily and retains 14 days.

CI runs lint + tests on every push and PR. On green CI to `main`, the deploy workflow
SSHes into the VPS, pulls, rebuilds the web image, restarts the stack, and smoke-tests
`/accounts/login/`.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full server bootstrap, secrets list, and rollback procedure.

## Roadmap

- [ ] Email notifications for follow-ups (currently visual-only)
- [ ] Tags / labels per application (in addition to status)
- [ ] Calendar view for upcoming interviews
- [ ] CSV / iCal export
- [ ] OAuth login (Google) as an alternative to email/password
- [ ] Sentry integration for prod error tracking
- [ ] PWA / offline mode for mobile

## License

MIT
