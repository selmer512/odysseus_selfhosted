#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/selmer512/odysseus_selfhosted.git}"
BRANCH="${BRANCH:-agentic-coding-implementation}"
OLD_DIR="${OLD_DIR:-$HOME/odysseus}"
NEW_DIR="${NEW_DIR:-$HOME/odysseus_selfhosted}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/odysseus-backups}"
APP_BIND="${APP_BIND:-127.0.0.1}"
APP_PORT="${APP_PORT:-7000}"

ts="$(date +%Y%m%d-%H%M%S)"
backup_dir="$BACKUP_ROOT/$ts"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

copy_if_present() {
  local src="$1"
  local dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
}

need git
need docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required: docker compose version failed" >&2
  exit 1
fi

mkdir -p "$backup_dir"

echo "Backing up old Odysseus deployment from: $OLD_DIR"
if [ -d "$OLD_DIR" ]; then
  copy_if_present "$OLD_DIR/.env" "$backup_dir/.env"
  copy_if_present "$OLD_DIR/docker-compose.yml" "$backup_dir/docker-compose.yml"
  copy_if_present "$OLD_DIR/compose.yml" "$backup_dir/compose.yml"
  copy_if_present "$OLD_DIR/data" "$backup_dir/data"
  copy_if_present "$OLD_DIR/logs" "$backup_dir/logs"
else
  echo "Old directory not found; continuing without old-directory backup."
fi

echo "Stopping old Compose stack without deleting volumes..."
if [ -d "$OLD_DIR" ]; then
  (cd "$OLD_DIR" && docker compose down --remove-orphans) || true
fi

if [ ! -d "$NEW_DIR/.git" ]; then
  echo "Cloning new Odysseus stack into: $NEW_DIR"
  git clone "$REPO_URL" "$NEW_DIR"
fi

cd "$NEW_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ ! -f .env ]; then
  if [ -f "$backup_dir/.env" ]; then
    echo "Restoring .env from old deployment backup."
    cp "$backup_dir/.env" .env
  else
    echo "Creating .env from .env.example. Fill in secrets after first boot if needed."
    cp .env.example .env
  fi
fi

if [ -d "$backup_dir/data" ] && [ ! -d data ]; then
  echo "Restoring data directory from old deployment backup."
  cp -a "$backup_dir/data" data
fi

if [ -d "$backup_dir/logs" ] && [ ! -d logs ]; then
  echo "Restoring logs directory from old deployment backup."
  cp -a "$backup_dir/logs" logs
fi

mkdir -p data logs

echo "Building and starting new Odysseus stack..."
APP_BIND="$APP_BIND" APP_PORT="$APP_PORT" docker compose up -d --build

echo
echo "Replacement complete."
echo "Backup: $backup_dir"
echo "New deployment: $NEW_DIR"
echo "Open: http://$APP_BIND:$APP_PORT"
echo
echo "Check status with:"
echo "  cd $NEW_DIR && docker compose ps"
echo "  cd $NEW_DIR && docker compose logs -f odysseus"
