#!/bin/bash
set -euo pipefail

# ================================

# 1) Migrations & static (ideal: rodar migrations fora do web, mas ok)
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput

# 2) Detectar vCPUs reais do CONTAINER (cgroups), não do host
detect_cpus() {
  # cgroups v1
  if [[ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us && -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]]; then
    quota=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)
    period=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)
    if [[ "$quota" -gt 0 && "$period" -gt 0 ]]; then
      echo $(( (quota + period - 1) / period ))  # ceil(quota/period)
      return
    fi
  fi
  # cgroups v2
  if [[ -r /sys/fs/cgroup/cpu.max ]]; then
    read quota period < /sys/fs/cgroup/cpu.max
    if [[ "$quota" != "max" && "$quota" -gt 0 && "$period" -gt 0 ]]; then
      echo $(( (quota + period - 1) / period ))
      return
    fi
  fi
  # fallback
  nproc
}

CPUS=$(detect_cpus)
# 3) Workers “saudáveis” para ASGI: poucos processos, 1 thread
#    regra base: 2*CPU+1 com um teto; override por env se quiser
BASE_WORKERS=$(( 2 * CPUS + 1 ))
MAX_WORKERS=${GUNICORN_WORKERS_MAX:-8}
MIN_WORKERS=${GUNICORN_WORKERS_MIN:-3}
WORKERS=$BASE_WORKERS
[[ $WORKERS -gt $MAX_WORKERS ]] && WORKERS=$MAX_WORKERS
[[ $WORKERS -lt $MIN_WORKERS ]] && WORKERS=$MIN_WORKERS

# 4) Timeouts e reciclagem
TIMEOUT=${GUNICORN_TIMEOUT:-60}                 # <= reduza de 600 para 60–90
GRACEFUL_TIMEOUT=${GUNICORN_GRACEFUL_TIMEOUT:-30}
KEEPALIVE=${GUNICORN_KEEPALIVE:-5}
MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-2000}
MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-200}

# 5) Logs (access log pode pesar; ajuste se tráfego alto)
ACCESS_LOGFILE=${GUNICORN_ACCESS_LOGFILE:--}    # "-" = stdout
ERROR_LOGFILE=${GUNICORN_ERROR_LOGFILE:--}

# 6) Opcional: economizar I/O de /tmp
WORKER_TMP_DIR=${GUNICORN_WORKER_TMP_DIR:-/dev/shm}

echo "[boot] CPUs=$CPUS, workers=$WORKERS, timeout=$TIMEOUT"

# 7) Start Gunicorn (ASGI + UvicornWorker, threads=1)
exec gunicorn service.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8882 \
  --workers "$WORKERS" \
  --threads 1 \
  --max-requests "$MAX_REQUESTS" \
  --max-requests-jitter "$MAX_REQUESTS_JITTER" \
  --timeout "$TIMEOUT" \
  --graceful-timeout "$GRACEFUL_TIMEOUT" \
  --keep-alive "$KEEPALIVE" \
  --worker-tmp-dir "$WORKER_TMP_DIR" \
  --proxy-allow-from="*" \
  --forwarded-allow-ips="*" \
  --access-logfile "$ACCESS_LOGFILE" \
  --error-logfile "$ERROR_LOGFILE"
