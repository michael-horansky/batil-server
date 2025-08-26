#!/bin/bash
# Start user A on port 5000
SESSION_COOKIE_NAME=session_5000 flask --app batil run --debug --port 5000 &
PID1=$!

# Start user B on port 5001
SESSION_COOKIE_NAME=session_5001 flask --app batil run --debug --port 5001 &
PID2=$!

echo "Flask apps started:"
echo "  User A: http://localhost:5000"
echo "  User B: http://localhost:5001"
echo "PIDs: $PID1, $PID2"

# Ensure both processes are killed when script exits (Ctrl+C etc.)
trap "kill $PID1 $PID2" EXIT

# Wait for both so Ctrl+C kills them
wait $PID1 $PID2
