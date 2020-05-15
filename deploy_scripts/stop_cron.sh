#!/bin/bash
set -e

echo "pkill cron"
# stop all running cron jobs
sudo pkill crond

echo "systemctl stop crond"
# stop cron
sudo systemctl stop crond

echo "done"
