#!/bin/bash
# Start Practice Manager web app in background (survives SSH disconnect)
# Run from VM: ~/Practice-Manager/deploy/start-app.sh
# Or: bash ~/Practice-Manager/deploy/start-app.sh

cd ~/Practice-Manager || exit 1
PYTHON=./venv/bin/python
[ -x "$PYTHON" ] || PYTHON=python3

# Ensure rclone mount is running (optional - uncomment if needed)
# if ! mountpoint -q /mnt/otpd-scores 2>/dev/null; then
#   echo "Mounting Drive..."
#   rclone mount gdrive:"OTPD Scores" /mnt/otpd-scores --vfs-cache-mode full --dir-cache-time 72h --daemon
#   sleep 2
# fi

# Kill existing uvicorn if running
pkill -f "uvicorn.*practice_manager" 2>/dev/null
sleep 1

# Start app in background (nohup keeps it running after SSH closes)
# Add AUTH_USERNAME and AUTH_PASSWORD for password protection, e.g.:
#   AUTH_USERNAME=myuser AUTH_PASSWORD=mypass nohup env ...
nohup env LIBRARY_ROOT=/mnt/otpd-scores \
  "$PYTHON" -m uvicorn src.practice_manager.web.main:app --host 0.0.0.0 --port 8000 \
  >> ~/Practice-Manager/app.log 2>&1 &

echo "Practice Manager started. PID: $!"
echo "Logs: tail -f ~/Practice-Manager/app.log"
echo "Stop: pkill -f uvicorn"
