#!/usr/bin/env bash
set -euo pipefail

OLD_DIR="${OLD_DIR:-$HOME/odysseus}"
NEW_DIR="${NEW_DIR:-$HOME/odysseus_selfhosted}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/odysseus-backups}"
CONFIRM="${CONFIRM_CLEAR_OLD_ODYSSEUS_DATA:-}"
SKIP_BACKUP="${SKIP_BACKUP:-0}"
REMOVE_DOCKER_VOLUMES="${REMOVE_DOCKER_VOLUMES:-1}"
REMOVE_IMAGES="${REMOVE_IMAGES:-0}"
DELETE_OLD_DIR="${DELETE_OLD_DIR:-1}"
OLD_PROJECT_NAME="${OLD_PROJECT_NAME:-}"

ts="$(date +%Y%m%d-%H%M%S)"
backup_dir="$BACKUP_ROOT/old-odysseus-cleared-$ts"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

real_or_raw() {
  if command -v realpath >/dev/null 2>&1; then
    realpath -m "$1"
  else
    printf '%s\n' "$1"
  fi
}

copy_if_present() {
  local src="$1"
  local dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
}

remove_prefixed_volumes() {
  local prefix="$1"
  if [ -z "$prefix" ]; then
    return 0
  fi
  docker volume ls --format '{{.Name}}' | awk -v p="${prefix}_" 'index($0,p)==1 {print}' | while read -r volume_name; do
    [ -n "$volume_name" ] || continue
    docker volume rm "$volume_name" || true
  done
}

if [ "$CONFIRM" != "YES" ]; then
  cat >&2 <<'MSG'
Refusing to clear data without explicit confirmation.

Run with:
  CONFIRM_CLEAR_OLD_ODYSSEUS_DATA=YES bash scripts/clear-old-odysseus-data.sh

Useful options:
  OLD_DIR=/path/to/old/odysseus
  NEW_DIR=/path/to/new/odysseus_selfhosted
  SKIP_BACKUP=1                 # do not keep a final backup
  REMOVE_DOCKER_VOLUMES=1        # default; removes old compose named volumes
  REMOVE_IMAGES=1                # also remove old compose-built images
  DELETE_OLD_DIR=1               # default; deletes the old folder after stopping
  OLD_PROJECT_NAME=name          # optional extra cleanup for volumes named name_*
MSG
  exit 2
fi

need docker

old_real="$(real_or_raw "$OLD_DIR")"
new_real="$(real_or_raw "$NEW_DIR")"

if [ "$old_real" = "$new_real" ]; then
  echo "OLD_DIR and NEW_DIR resolve to the same path. Refusing to delete: $old_real" >&2
  exit 1
fi

if [ ! -d "$OLD_DIR" ]; then
  echo "Old Odysseus directory does not exist: $OLD_DIR"
  echo "Nothing to clear from disk."
else
  if [ "$SKIP_BACKUP" != "1" ]; then
    echo "Creating final backup before clearing old data: $backup_dir"
    mkdir -p "$backup_dir"
    copy_if_present "$OLD_DIR/.env" "$backup_dir/.env"
    copy_if_present "$OLD_DIR/docker-compose.yml" "$backup_dir/docker-compose.yml"
    copy_if_present "$OLD_DIR/compose.yml" "$backup_dir/compose.yml"
    copy_if_present "$OLD_DIR/data" "$backup_dir/data"
    copy_if_present "$OLD_DIR/logs" "$backup_dir/logs"
  else
    echo "SKIP_BACKUP=1 set; no final backup will be created."
  fi

  echo "Stopping old Docker Compose stack from: $OLD_DIR"
  if [ "$REMOVE_DOCKER_VOLUMES" = "1" ]; then
    (cd "$OLD_DIR" && docker compose down -v --remove-orphans) || true
  else
    (cd "$OLD_DIR" && docker compose down --remove-orphans) || true
  fi

  if [ "$REMOVE_IMAGES" = "1" ]; then
    echo "Removing old Compose-built images where Compose can identify them."
    (cd "$OLD_DIR" && docker compose down --rmi local --remove-orphans) || true
  fi

  if [ "$DELETE_OLD_DIR" = "1" ]; then
    echo "Deleting old Odysseus directory: $OLD_DIR"
    rm -rf -- "$OLD_DIR"
  else
    echo "Deleting old Odysseus runtime data inside: $OLD_DIR"
    rm -rf -- "$OLD_DIR/data" "$OLD_DIR/logs" "$OLD_DIR/.env" "$OLD_DIR/.env.local"
  fi
fi

if [ -n "$OLD_PROJECT_NAME" ] && [ "$REMOVE_DOCKER_VOLUMES" = "1" ]; then
  echo "Removing additional Docker volumes with prefix: ${OLD_PROJECT_NAME}_"
  remove_prefixed_volumes "$OLD_PROJECT_NAME"
fi

echo
echo "Old Odysseus data clear complete."
if [ "$SKIP_BACKUP" != "1" ]; then
  echo "Final backup: $backup_dir"
fi
echo "New deployment path was protected: $NEW_DIR"
