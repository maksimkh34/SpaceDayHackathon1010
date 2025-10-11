@echo off
cd /d %~dp0
echo 🚀 Starting JavaServer in development mode...

set SPRING_PROFILES_ACTIVE=local
set ML_SERVICE_URL=http://localhost:5000

echo Active profile: %SPRING_PROFILES_ACTIVE%
echo ML Service URL: %ML_SERVICE_URL%

gradlew bootRun
pause
