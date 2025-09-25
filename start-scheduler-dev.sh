#!/bin/bash
./wait-for-it.sh -t 0 previta-service:8882 -- echo "API IS UP"
python manage.py celery_worker