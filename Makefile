up:
	docker-compose -f docker-compose.yml stop && docker-compose -f docker-compose.yml up
watch:	
	docker-compose -f docker-compose.yml stop && docker-compose -f docker-compose.yml up -d && docker logs -f --since 5m previta-service
watch-scheduler:	
	docker-compose -f docker-compose.yml stop && docker-compose -f docker-compose.yml up -d && docker logs -f --since 5m previta-service
watch-evolution:	
	docker-compose -f docker-compose.yml stop && docker-compose -f docker-compose.yml up -d && docker logs -f --since 5m previta-service
stop:
	docker-compose -f docker-compose.yml stop
down:
	docker-compose -f docker-compose.yml down -v	
build:
	docker-compose -f docker-compose.yml down && docker-compose -f docker-compose.yml up --build previta-service previta-scheduler && docker logs -f previta-service

build-all:
	docker-compose -f docker-compose.yml down && docker-compose -f docker-compose.yml up --build previta-service previta-scheduler previta-evolution && docker logs -f previta-service

bash:
	docker exec -it previta-service bash
	
bash-scheduler:
	docker exec -it previta-scheduler bash

bash-evolution:
	docker exec -it previta-evolution bash

deploy: # não aplica nada ao evolution
	docker compose -f docker-compose-prod.yml stop previta-service previta-scheduler && git pull && docker compose -f docker-compose-prod.yml up -d --build previta-service previta-scheduler

run: #não aplica nada ao evolution
	docker compose -f docker-compose-prod.yml stop previta-service previta-scheduler && docker compose -f docker-compose-prod.yml up -d previta-service previta-scheduler

deploy-all: # aplica a todas as partes
	docker compose -f docker-compose-prod.yml stop previta-service previta-scheduler previta-evolution && git pull && docker compose -f docker-compose-prod.yml up -d --build previta-service previta-scheduler previta-evolution

run-all: # aplica a todas as partes
	docker compose -f docker-compose-prod.yml stop previta-service previta-scheduler previta-evolution && docker compose -f docker-compose-prod.yml up -d previta-service previta-scheduler previta-evolution

deploy-evolution:
	docker compose -f docker-compose-prod.yml stop previta-evolution && git pull && docker compose -f docker-compose-prod.yml up -d --build previta-evolution

run-evolution:
	docker compose -f docker-compose-prod.yml stop previta-evolution && docker compose -f docker-compose-prod.yml up -d previta-evolution

scheduler-logs:
	docker logs -f --since 10m previta-scheduler

service-logs:
	docker logs -f --since 10m previta-service

evolution-logs:
	docker logs -f --since 10m previta-evolution


SINCE ?= 30s
QUERY ?= 

# Busca blocos que contenham QUERY, imprimindo do "[Evolution API]" até o próximo
evo-logs-parser:
	@docker logs -f --since $(SINCE) previta-evolution | \
	awk -v needle="$(QUERY)" '\
	BEGIN {color_start="\033[1;31m"; color_end="\033[0m"} \
	/\[Evolution API\]/ { if (found) { print bloco "\n" } bloco=""; found=0 } \
	{ \
		line=$$0; \
		gsub(needle, color_start needle color_end, line); \
		bloco = bloco line ORS \
	} \
	$$0 ~ needle { found=1 } \
	END { if (found) print bloco }'

# Atalhos por serviço (podem sobrescrever CONTAINER/SINCE/QUERY se quiser)
evolution-logs-search:
	@$(MAKE) evo-logs-parser
	
clean:
	docker-compose -f docker-compose.yml down --remove-orphans
	docker container prune -f
	docker system prune -f


run-grafana:
	docker compose -f docker-compose-logs.yml stop loki promtail grafana && docker compose -f docker-compose-logs.yml up -d

stop-grafana:
	docker compose -f docker-compose-logs.yml stop loki promtail grafana