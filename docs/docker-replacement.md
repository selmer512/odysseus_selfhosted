# Replace an old Odysseus Docker deployment

This guide replaces an older Odysseus Docker setup with the current `agentic-coding-implementation` stack while preserving old data first.

## What the new stack runs

The current Docker Compose stack starts:

- `odysseus` web app on `${APP_BIND:-127.0.0.1}:${APP_PORT:-7000}:7000`
- `chromadb` on `${CHROMADB_BIND:-127.0.0.1}:8100:8000`
- `searxng` on `127.0.0.1:8080:8080`
- `ntfy` on `${NTFY_BIND:-127.0.0.1}:8091:80`

The app persists host data under:

- `${APP_DATA_DIR:-./data}` mounted to `/app/data`
- `${APP_LOGS_DIR:-./logs}` mounted to `/app/logs`

## Safe replacement script

From any directory on the host:

```bash
curl -fsSL https://raw.githubusercontent.com/selmer512/odysseus_selfhosted/agentic-coding-implementation/scripts/replace-odysseus-docker.sh -o replace-odysseus-docker.sh
bash replace-odysseus-docker.sh
```

Defaults:

```bash
OLD_DIR=$HOME/odysseus
NEW_DIR=$HOME/odysseus_selfhosted
BRANCH=agentic-coding-implementation
APP_BIND=127.0.0.1
APP_PORT=7000
BACKUP_ROOT=$HOME/odysseus-backups
```

Override them when needed:

```bash
OLD_DIR=/opt/old-odysseus \
NEW_DIR=/opt/odysseus_selfhosted \
APP_BIND=100.x.y.z \
APP_PORT=7000 \
bash replace-odysseus-docker.sh
```

## Manual replacement steps

```bash
OLD_DIR=$HOME/odysseus
NEW_DIR=$HOME/odysseus_selfhosted
BACKUP_ROOT=$HOME/odysseus-backups
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_ROOT/$STAMP"
```

Back up the old deployment:

```bash
cp -a "$OLD_DIR/.env" "$BACKUP_ROOT/$STAMP/.env" 2>/dev/null || true
cp -a "$OLD_DIR/data" "$BACKUP_ROOT/$STAMP/data" 2>/dev/null || true
cp -a "$OLD_DIR/logs" "$BACKUP_ROOT/$STAMP/logs" 2>/dev/null || true
cp -a "$OLD_DIR/docker-compose.yml" "$BACKUP_ROOT/$STAMP/docker-compose.yml" 2>/dev/null || true
```

Stop the old stack without deleting volumes:

```bash
cd "$OLD_DIR"
docker compose down --remove-orphans
```

Clone or update the new stack:

```bash
git clone https://github.com/selmer512/odysseus_selfhosted.git "$NEW_DIR" 2>/dev/null || true
cd "$NEW_DIR"
git fetch origin agentic-coding-implementation
git checkout agentic-coding-implementation
git pull --ff-only origin agentic-coding-implementation
```

Restore environment and data if this is a new directory:

```bash
[ -f .env ] || cp "$BACKUP_ROOT/$STAMP/.env" .env 2>/dev/null || cp .env.example .env
[ -d data ] || cp -a "$BACKUP_ROOT/$STAMP/data" data 2>/dev/null || mkdir -p data
[ -d logs ] || cp -a "$BACKUP_ROOT/$STAMP/logs" logs 2>/dev/null || mkdir -p logs
```

Start the new stack:

```bash
docker compose up -d --build
```

Check it:

```bash
docker compose ps
docker compose logs -f odysseus
```

Open:

```text
http://127.0.0.1:7000
```

## Common port conflicts

If port `7000` is already used:

```bash
echo 'APP_PORT=7001' >> .env
docker compose up -d --build
```

If exposing over Tailscale, keep it private to your tailnet:

```bash
echo 'APP_BIND=100.x.y.z' >> .env
echo 'APP_PORT=7000' >> .env
docker compose up -d --build
```

## Do not run this unless intentionally wiping data

Do **not** use `docker compose down -v` during replacement. `-v` deletes named volumes such as ChromaDB, SearXNG, and ntfy cache.
