import shlex
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.utils import autoreload


def restart_celery():
    celery_worker_cmd = "celery -A service.celery worker -B"
    cmd = f'pkill -f "{celery_worker_cmd}"'
    
    subprocess.call(shlex.split(cmd))
    cmd = f'{celery_worker_cmd} -l info'
    subprocess.call(shlex.split(cmd)) 


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('Starting celery worker with autoreload...')
        autoreload.run_with_reloader(restart_celery)