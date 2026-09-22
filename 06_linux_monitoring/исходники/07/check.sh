#!/bin/bash

# Проверяет сервисы, HTTP-интерфейсы и наличие системных метрик.
failed=0

for service in prometheus prometheus-node-exporter grafana-server; do
    if systemctl is-active --quiet "$service"; then
        echo "OK: $service работает"
    else
        echo "FAIL: $service не работает"
        failed=1
    fi
done

curl -fsS http://localhost:9090/-/ready >/dev/null &&
    echo "OK: Prometheus готов" || { echo "FAIL: Prometheus"; failed=1; }

curl -fsS http://localhost:9100/metrics |
    awk '/^node_cpu_seconds_total/ { found=1 } END { exit !found }' &&
    echo "OK: Node Exporter отдаёт метрики" ||
    { echo "FAIL: Node Exporter"; failed=1; }

curl -fsS http://localhost:3000/api/health |
    grep -Eq '"database"[[:space:]]*:[[:space:]]*"ok"' &&
    echo "OK: Grafana готова" || { echo "FAIL: Grafana"; failed=1; }

exit "$failed"
