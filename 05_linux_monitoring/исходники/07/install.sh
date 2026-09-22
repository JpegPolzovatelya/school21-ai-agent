#!/bin/bash
set -e

# Устанавливает Prometheus, Node Exporter, stress и зависимости Grafana.
sudo apt-get update
sudo apt-get install -y prometheus prometheus-node-exporter stress \
    apt-transport-https wget gnupg

# Добавляет официальный ключ и стабильный APT-репозиторий Grafana.
sudo mkdir -p /etc/apt/keyrings
sudo wget -qO /etc/apt/keyrings/grafana.asc \
    https://apt.grafana.com/gpg-full.key
sudo chmod 644 /etc/apt/keyrings/grafana.asc

echo "deb [signed-by=/etc/apt/keyrings/grafana.asc] https://apt.grafana.com stable main" |
    sudo tee /etc/apt/sources.list.d/grafana.list >/dev/null

sudo apt-get update
sudo apt-get install -y grafana

echo "Установка завершена."
