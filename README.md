# Job Tracker

Outil personnel de suivi de candidatures, construit avec Django.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.x-green?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![CI](https://github.com/C0X23/job-tracker/actions/workflows/ci.yml/badge.svg)

> **Démo live** : [job-tracker.cmegret.com](https://job-tracker.cmegret.com) *(Sprint 5)*

---

## Fonctionnalités

- **CRUD candidatures** — statut, source, salaire, lien d'annonce, mode (présentiel/hybride/remote), CV, lettre de motivation
- **Contacts** — recruteurs / managers liés à une candidature, édition inline via htmx
- **Timeline** — historique d'événements (entretiens, relances, notes), changements de statut auto-trackés
- **Notes en Markdown** — rendu sécurisé (échappement HTML), gras / listes / liens / tables / blocs de code
- **Dashboard** — alertes "à relancer aujourd'hui" en évidence, candidatures actives
- **Stats** — funnel de conversion, distribution par statut/source, volume hebdomadaire (Chart.js)
- **API REST** — endpoints DRF authentifiés sous `/api/v1/stats/`
- **htmx + Alpine.js** — pas de rechargement pour les actions courantes (changement de statut, ajout de contact, événement)

## Stack

| Couche | Technologie |
|---|---|
| Backend | Django 5.x + Django REST Framework |
| Base de données | PostgreSQL 16 |
| Frontend | Templates Django + htmx + Alpine.js + Tailwind CSS (CDN) |
| Auth | django-allauth (login par email) |
| Markdown | markdown2 (mode safe) |
| Conteneurisation | Docker + docker-compose |
| Reverse proxy | Caddy *(Sprint 5)* |
| CI/CD | GitHub Actions |
| Tests | pytest-django + factory_boy (97% de couverture) |
| Qualité | ruff + black + mypy strict |

## Démarrage local

```bash
git clone https://github.com/C0X23/job-tracker.git
cd job-tracker
cp .env.example .env
docker compose up --build
```

Puis, dans un second terminal :

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Ouvrir [http://localhost:8000](http://localhost:8000).

## Structure

```
applications/      # Candidatures, contacts, timeline (modèles, vues, htmx)
accounts/          # Wrapper allauth + templates de login
stats/             # Endpoints DRF d'agrégation + page Chart.js

config/            # settings (base/dev/prod), urls, wsgi
templates/         # base.html (templates app-spécifiques dans chaque app/templates/)
tests/             # pytest, un sous-dossier par app
docker/            # Dockerfile + Caddyfile
```

## Tests

```bash
docker compose exec web pytest --cov=applications --cov=stats
```

Ou localement (avec un `.env` configuré ou `DATABASE_URL=sqlite:///test.sqlite3`) :

```bash
pip install ".[dev]"
pytest --cov=applications --cov=stats
```

Lint et formatage :

```bash
ruff check .
black --check .
```

## API

| Endpoint | Description |
|---|---|
| `GET /api/v1/stats/summary/` | Total / actives / à relancer / cette semaine |
| `GET /api/v1/stats/status/` | Distribution par statut |
| `GET /api/v1/stats/source/` | Distribution par source |
| `GET /api/v1/stats/weekly/?weeks=12` | Volume par semaine (1–52) |
| `GET /api/v1/stats/funnel/` | Funnel de conversion cumulatif |

Authentification par session Django (les pages web et l'API partagent la même session).

## Licence

MIT
