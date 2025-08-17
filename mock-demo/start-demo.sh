#!/bin/bash

echo "Starting AI Governance Dashboard Mock Demo..."
echo ""
echo "This will start both the mock API server and the frontend."
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start both servers concurrently
npm start
