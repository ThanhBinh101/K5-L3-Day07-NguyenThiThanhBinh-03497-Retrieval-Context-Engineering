#!/bin/zsh
setopt NO_BG_NICE
cd "${0:A:h}"
TASK_PYTHON="${DAY07_PYTHON:-../K5-L3-Day06-NguyenThiThanhBinh-MSSV-DataIngestionEngineering/.venv/bin/python}"
if [[ ! -x "$TASK_PYTHON" ]]; then
  TASK_PYTHON=".venv/bin/python"
fi
if [[ ! -x "$TASK_PYTHON" ]]; then
  echo 'Chưa có Python environment. Đọc docs/RUN.md để cài đặt.'
  exit 1
fi
if /usr/bin/curl --silent --fail 'http://127.0.0.1:8707/api/status' >/dev/null; then
  open 'http://127.0.0.1:8707'
  exit 0
fi
"$TASK_PYTHON" -m src.web --port 8707 &
TASK_SERVER_PID=$!
trap 'kill "$TASK_SERVER_PID" 2>/dev/null' EXIT INT TERM HUP
for TASK_ATTEMPT in {1..60}; do
  if /usr/bin/curl --silent --fail 'http://127.0.0.1:8707/api/status' >/dev/null; then
    open 'http://127.0.0.1:8707'
    break
  fi
  sleep 0.2
done
wait "$TASK_SERVER_PID"
