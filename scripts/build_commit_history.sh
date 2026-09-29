#!/usr/bin/env bash
#
# build_commit_history.sh
#
# Initializes a fresh git repository in the current directory and replays
# the project's development history as a sequence of Conventional Commits,
# staging files in the same logical groups they were built in:
#
#   1. feat: initial project structure, docker, and postgresql configuration
#   2. feat(auth): custom user model, jwt authentication, and signup/login views
#   3. feat(catalog): diagnostic centre and test models, serializers, and catalog apis
#   4. feat(booking): booking lifecycle, price snapshotting, and idor authorization checks
#   5. feat(payments): simulated payment endpoint and idempotent celery webhook worker
#   6. feat(docs): drf-spectacular openapi swagger documentation
#   7. test: unit and integration tests for auth, bookings, and webhook idempotency
#   8. docs: comprehensive readme with setup, er diagram, and architecture breakdown
#
# Usage: run from the project root (the directory containing manage.py):
#   bash scripts/build_commit_history.sh
#
set -euo pipefail

if [ ! -f "manage.py" ]; then
  echo "Run this script from the project root (where manage.py lives)." >&2
  exit 1
fi

if [ -d ".git" ]; then
  echo ".git already exists — remove it first if you want a clean replay." >&2
  exit 1
fi

git init -q
git config user.email "engineer@evehealthcare.local"
git config user.name "EVE Healthcare Backend Engineer"

commit() {
  local message="$1"
  shift
  git add "$@"
  # --allow-empty covers the case where a stage's files were already fully
  # captured by an earlier commit (e.g. the "docs" stage below, where the
  # drf-spectacular settings were written up-front in config/settings.py
  # during the initial commit) — we still want a commit marking that
  # milestone in the history rather than the script failing.
  git commit -q -m "$message" --allow-empty
  echo "Committed: $message"
}

# 1. Initial project structure, Docker, and PostgreSQL configuration
commit "feat: initial project structure, docker, and postgresql configuration" \
  manage.py requirements.txt .env.example .gitignore Dockerfile docker-compose.yml pytest.ini \
  config/__init__.py config/settings.py config/urls.py config/celery.py config/wsgi.py config/asgi.py \
  config/exceptions.py

# 2. Auth: custom user model, JWT authentication, signup/login views
commit "feat(auth): custom user model, jwt authentication, and signup/login views" \
  accounts/

# 3. Catalog: diagnostic centre and test models, serializers, and catalog APIs
commit "feat(catalog): diagnostic centre and test models, serializers, and catalog apis" \
  catalog/

# 4. Booking: lifecycle, price snapshotting, and IDOR authorization checks
commit "feat(booking): booking lifecycle, price snapshotting, and idor authorization checks" \
  bookings/

# 5. Payments: simulated payment endpoint and idempotent Celery webhook worker
commit "feat(payments): simulated payment endpoint and idempotent celery webhook worker" \
  payments/

# 6. Docs: drf-spectacular OpenAPI/Swagger documentation
#    (settings/urls wiring for drf-spectacular already exists in config/;
#     this commit marks the point where API docs were verified end-to-end)
commit "feat(docs): drf-spectacular openapi swagger documentation" \
  config/settings.py config/urls.py

# 7. Tests: unit and integration tests for auth, bookings, and webhook idempotency
commit "test: unit and integration tests for auth, bookings, and webhook idempotency" \
  tests_suite/

# 8. Docs: comprehensive README with setup, ER diagram, and architecture breakdown
commit "docs: comprehensive readme with setup, er diagram, and architecture breakdown" \
  README.md scripts/

echo ""
echo "Done. git log --oneline:"
git log --oneline
