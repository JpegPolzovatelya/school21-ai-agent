#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Проверяет конфигурацию Prometheus до её установки.
if command -v promtool >/dev/null 2>&1; then
    promtool check config "$SCRIPT_DIR/prometheus.yml"
fi

# Устанавливает конфигурацию Prometheus.
sudo install -m 644 "$SCRIPT_DIR/prometheus.yml" \
    /etc/prometheus/prometheus.yml

# Устанавливает автоматическую настройку Grafana.
sudo mkdir -p /etc/grafana/provisioning/datasources
sudo mkdir -p /etc/grafana/provisioning/dashboards
sudo mkdir -p /var/lib/grafana/dashboards
sudo install -m 644 "$SCRIPT_DIR/datasource.yml" \
    /etc/grafana/provisioning/datasources/prometheus.yml
sudo install -m 644 "$SCRIPT_DIR/dashboard-provider.yml" \
    /etc/grafana/provisioning/dashboards/linux.yml
sudo install -m 644 "$SCRIPT_DIR/dashboard.json" \
    /var/lib/grafana/dashboards/linux-monitoring.json
sudo chown -R grafana:grafana /var/lib/grafana/dashboards

# Запускает сервисы сейчас и при последующих загрузках системы.
sudo systemctl enable --now prometheus
sudo systemctl enable --now prometheus-node-exporter
sudo systemctl enable --now grafana-server
sudo systemctl restart prometheus prometheus-node-exporter grafana-server

echo "Настройка завершена."
echo "Prometheus: http://localhost:9090"
echo "Grafana:    http://localhost:3000"
