
140: docker compose up -d                                  # backend, redis, ai_worker, frontend
141: docker compose --profile observability up -d          # adds Prometheus, Grafana, Loki, Promtail, Tempo, ntfy and the exporters
142: # Grafana: http://localhost:3000 (user admin; the password is the gitignored secret file docker/secrets/grafana_admin_password)
