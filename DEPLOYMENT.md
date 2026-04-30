# Deployment

Production target: a single Hetzner Cloud VM (CX22 / CX32) running Docker Compose with Caddy as reverse proxy. Caddy obtains and renews TLS certificates automatically via Let's Encrypt.

## Architecture

```
                ┌──────────────────────────────────────────────┐
   Internet ──► │ Caddy (TLS, gzip, security headers, static)  │
                └─────────────┬────────────────────────────────┘
                              │ reverse_proxy http://web:8000
                ┌─────────────▼────────────────────────────────┐
                │ web (gunicorn → Django, prod settings)       │
                └─────────────┬────────────────────────────────┘
                              │
                ┌─────────────▼────────────┐  ┌──────────────────┐
                │ db (postgres:16-alpine)  │  │ backup (pg_dump) │
                └──────────────────────────┘  └──────────────────┘
```

## Prerequisites

- A Hetzner Cloud VM (Ubuntu 24.04 LTS recommended)
- A domain with an A record pointing to the VM's IP (e.g. `job-tracker.cmegret.com`)
- An SSH key registered on the VM for the deploy user

## Server bootstrap (once)

```bash
# As root, create a deploy user
adduser deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh

# Install Docker + Compose plugin
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy

# As deploy user
su - deploy
git clone https://github.com/C0X23/job-tracker.git /home/deploy/job-tracker
cd /home/deploy/job-tracker
cp .env.prod.example .env.prod
# Edit .env.prod: SECRET_KEY, DOMAIN, ALLOWED_HOSTS, POSTGRES_PASSWORD, DATABASE_URL
nano .env.prod

# First boot
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Create the first user
docker compose exec web python manage.py createsuperuser
```

Caddy will request a TLS certificate from Let's Encrypt on its first run. Watch the logs:

```bash
docker compose logs -f caddy
```

## Generating SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Continuous deployment

The [`Deploy`](.github/workflows/deploy.yml) workflow runs after a successful CI run on `main` (or via manual dispatch). It SSHes into the VM, pulls the latest code, rebuilds the `web` image, and restarts the stack.

Required GitHub repository secrets:

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | VM IP or hostname |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_PATH` | `/home/deploy/job-tracker` |
| `DEPLOY_SSH_KEY` | Private SSH key with access to the deploy user |
| `DEPLOY_DOMAIN` | `job-tracker.cmegret.com` (used by the smoke test) |

## Backups

The `backup` service runs `pg_dump` once every 24 hours and writes gzipped dumps to `./backups/` on the host. Files older than 14 days are pruned automatically.

To restore a dump:

```bash
gunzip -c backups/jobtracker_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

For off-site backups, sync the `backups/` directory to S3 / Backblaze / Hetzner Storage Box with `restic` or `rclone`.

## Useful commands

```bash
# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web

# Run a Django shell
docker compose exec web python manage.py shell

# Apply migrations manually (the web entrypoint does this, but useful in a pinch)
docker compose exec web python manage.py migrate

# Restart only the web service
docker compose restart web
```

## Rolling back

```bash
cd /home/deploy/job-tracker
git log --oneline -10                # find the last good commit
git reset --hard <sha>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build web
```

If a migration is the problem, also restore from the latest pg_dump before redeploying.
