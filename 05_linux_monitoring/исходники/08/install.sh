#!/bin/bash
set -e

# iperf3 нужен на обеих виртуальных машинах.
sudo apt-get update
sudo apt-get install -y iperf3

echo "iperf3 установлен."
