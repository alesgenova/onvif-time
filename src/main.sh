#!/bin/sh

# Sync time on startup
STARTUP_SYNC_LOWER="$(echo "$ONVIF_TIME_STARTUP_SYNC" | tr '[:upper:]' '[:lower:]')"
if [ "$STARTUP_SYNC_LOWER" == "true" ]; then
  python3 /src/onvif_time.py
fi

# Add cron job to run the time sync script
echo "${ONVIF_TIME_SCHEDULE} python3 /src/onvif_time.py" > /etc/crontabs/root

# Run crond in the foreground
crond -f
