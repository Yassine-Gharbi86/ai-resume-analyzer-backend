#!/usr/bin/env bash
# build.sh — Render runs this script during every deployment.
# It installs dependencies, collects static files, and applies migrations.

set -o errexit  # exit immediately if any command fails

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
