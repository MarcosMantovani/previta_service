#!/bin/bash
set -euo pipefail

./wait-for-it.sh -t 0 previta-service:8882 -- echo "API IS UP"

# CPUs visíveis ao container (cgroups-aware)
detect_cpus() {
  if [[ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us && -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]]; then
    q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us); p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)
    if [[ "$q" -gt 0 && "$p" -gt 0 ]]; then echo $(( (q + p - 1) / p )); return; fi
  fi
  if [[ -r /sys/fs/cgroup/cpu.max ]]; then
    read q p < /sys/fs/cgroup/cpu.max
    if [[ "$q" != "max" && "$q" -gt 0 && "$p" -gt 0 ]]; then echo $(( (q + p - 1) / p )); return; fi
  fi
  nproc
}
CPUS=$(detect_cpus)

# Concurrency “saudável”
IS_IO_BOUND=${CELERY_IO_BOUND:-0}         # 0=CPU-bound, 1=IO-bound
if [[ "$IS_IO_BOUND" == "1" ]]; then
  BASE_CONC=$(( CPUS + (CPUS/2) ))       # ~1.5x CPUs
else
  BASE_CONC=$(( CPUS ))                   # ~1.0x CPUs
fi
MIN_CONC=${CELERY_MIN_CONCURRENCY:-3}
MAX_CONC=${CELERY_MAX_CONCURRENCY:-10}
CONCURRENCY=${CELERY_CONCURRENCY:-$BASE_CONC}
[[ $CONCURRENCY -lt $MIN_CONC ]] && CONCURRENCY=$MIN_CONC
[[ $CONCURRENCY -gt $MAX_CONC ]] && CONCURRENCY=$MAX_CONC

# Pool e limites
POOL=${CELERY_POOL:-prefork}              # prefork padrão; gevent só se compatível
PREFETCH=${CELERY_PREFETCH:-1}            # 1 evita “estocar” tasks nos filhos
MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD:-500}
TIME_LIMIT=${CELERY_TIME_LIMIT:-120}
SOFT_TIME_LIMIT=${CELERY_SOFT_TIME_LIMIT:-90}
MAX_MEM_PER_CHILD=${CELERY_MAX_MEM_PER_CHILD:-600000}  # ~600MB
LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

# Beat junto: persistir agenda e ajustar loop
SCHEDULE_FILE=${CELERY_BEAT_SCHEDULE:-/data/celerybeat-schedule.db}  # monte /data no container
MAX_INTERVAL=${CELERY_BEAT_MAX_INTERVAL:-30}  # s (evita loop muito apertado)
TZ=${TZ:-America/Sao_Paulo}                   # importante pro agendamento

# flags para reduzir barulho de cluster
WITHOUT_GOSSIP=${CELERY_WITHOUT_GOSSIP:-1}
WITHOUT_MINGLE=${CELERY_WITHOUT_MINGLE:-1}
WITHOUT_HEARTBEAT=${CELERY_WITHOUT_HEARTBEAT:-0}

echo "[celery] cpus=$CPUS conc=$CONCURRENCY pool=$POOL prefetch=$PREFETCH max_tasks_per_child=$MAX_TASKS_PER_CHILD beat_schedule=$SCHEDULE_FILE"

CMD=( celery -A service worker -B
      -l "$LOGLEVEL"
      --pool "$POOL"
      --concurrency "$CONCURRENCY"
      --prefetch-multiplier "$PREFETCH"
      --max-tasks-per-child "$MAX_TASKS_PER_CHILD"
      --time-limit "$TIME_LIMIT"
      --soft-time-limit "$SOFT_TIME_LIMIT"
      --max-memory-per-child "$MAX_MEM_PER_CHILD"
      --schedule "$SCHEDULE_FILE"
      --hostname "celery@$(hostname -s)"    # evita confusão de lock se reiniciar
      --pidfile /tmp/celery-worker.pid
    )

[[ "$WITHOUT_GOSSIP" == "1" ]] && CMD+=( --without-gossip )
[[ "$WITHOUT_MINGLE" == "1" ]] && CMD+=( --without-mingle )
[[ "$WITHOUT_HEARTBEAT" == "1" ]] && CMD+=( --without-heartbeat )

export TZ
exec "${CMD[@]}"
