#!/bin/bash
# Double-click this file in Finder to launch your slides

cd "$(dirname "$0")"

# Kill any existing server on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start server
python3 -m http.server 8080 &
SERVER_PID=$!

sleep 0.8

# Open the latest slides in default browser
open "http://localhost:8080/brian-halligan-ceo-coach-slides.html"

echo "✓ Slides server running at http://localhost:8080"
echo "  Press Ctrl+C or close this window to stop."

# Keep running until user closes the window
wait $SERVER_PID
