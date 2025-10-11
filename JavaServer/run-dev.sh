#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting JavaServer in development mode..."

# Set development environment
export SPRING_PROFILES_ACTIVE=local
export ML_SERVICE_URL=http://localhost:5000

echo "Active profile: $SPRING_PROFILES_ACTIVE"
echo "ML Service URL: $ML_SERVICE_URL"

./gradlew bootRun
