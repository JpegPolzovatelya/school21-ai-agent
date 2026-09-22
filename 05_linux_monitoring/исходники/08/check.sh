#!/bin/bash

failed=0

# Проверяем компоненты мониторинга из части 7.
for service in prometheus prometheus-node-exporter grafana-server; do
    if systemctl is-active --quiet "$service"; then
        echo "OK: $service работает"
    else
        echo "FAIL: $service не работает"
        failed=1
    fi
done

if command -v iperf3 >/dev/null 2>&1; then
    echo "OK: iperf3 установлен"
else
    echo "FAIL: iperf3 не установлен"
    failed=1
fi

# Проверяем, что Node Exporter отдаёт сетевые метрики.
if curl -fsS http://localhost:9100/metrics |
    awk '/^node_network_receive_bytes_total/ { found=1 }
         END { exit !found }'; then
    echo "OK: сетевые метрики доступны"
else
    echo "FAIL: сетевые метрики недоступны"
    failed=1
fi

exit "$failed"
