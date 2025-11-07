#!/bin/bash
# Start all processes in the background and forward signals

# Start Gunicorn (web server)
gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 8 --timeout 0 test.asgi:application -k uvicorn.workers.UvicornWorker &
GUNICORN_PID=$!

# Start Celery worker
celery -A test worker -l INFO --pool gevent --concurrency 20 &
WORKER_PID=$!

# Start Celery beat (scheduler)
celery -A test beat -l INFO &
BEAT_PID=$!

# Function to kill all processes on exit
cleanup() {
    echo "Shutting down all processes..."
    kill $GUNICORN_PID $WORKER_PID $BEAT_PID 2>/dev/null
    wait $GUNICORN_PID $WORKER_PID $BEAT_PID 2>/dev/null
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Wait for all processes
wait

