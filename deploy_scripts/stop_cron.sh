#!/bin/bash
set -e

# stop all running cron jobs
if [[ `pgrep crond` ]]; then
  sudo pkill crond
fi

# stop cron
sudo systemctl stop crond
