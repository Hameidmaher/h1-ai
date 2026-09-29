#!/bin/bash
cd ~/h1-ai/tests/load
export WEBHOOK_API_KEY=$(grep "^WEBHOOK_API_KEY=" ~/h1-ai/backend/.env | cut -d= -f2)
export ADMIN_USER=admin
export ADMIN_PASS=admin123
. ~/h1-ai/backend/.venv/bin/activate
locust -f locustfile.py --host http://localhost:8000 --headless \
    -u 200 -r 20 -t 120s --only-summary --csv=heavy
