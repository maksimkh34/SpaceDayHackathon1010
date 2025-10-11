#!/usr/bin/env python3
"""
Project Refactor Script
Automates project cleanup and configuration
"""

import os
import shutil
import stat
from pathlib import Path

def create_file(path, content):
    """Create file with content"""
    directory = os.path.dirname(path)
    if directory:  # Only create directories if path contains them
        os.makedirs(directory, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Created: {path}")

def make_executable(path):
    """Make file executable"""
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def cleanup_project():
    """Remove unnecessary files and folders"""
    items_to_remove = [
        # Мусорные папки
        "frontend/backend",
        "ML/__pycache__",
        "ML/imgs",
        "ML/sample_img",
        ".idea",
        
        # Временные файлы
        "frontend/backend/uploads",
    ]
    
    for item in items_to_remove:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
                print(f"🗑️  Removed directory: {item}")
            else:
                os.remove(item)
                print(f"🗑️  Removed file: {item}")

def create_gitignore():
    """Create comprehensive .gitignore"""
    gitignore_content = """# IDE
.idea/
*.iml
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store

# Java
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar
!**/src/main/**/build/
!**/src/test/**/build/

# Logs
logs
*.log

# Database
*.db
*.sqlite
*.h2.db

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Uploads
uploads/
*/uploads/

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db

# ML models and large files
*.pkl
*.h5
*.model
*.weights
"""
    create_file(".gitignore", gitignore_content)

def create_scripts():
    """Create all necessary scripts"""
    
    # Docker запуск
    create_file("start-docker.sh", """#!/bin/bash
echo "🚀 Starting all services with Docker Compose..."
docker-compose up --build
""")
    
    create_file("start-docker.bat", """@echo off
echo 🚀 Starting all services with Docker Compose...
docker-compose up --build
pause
""")
    
    # Индивидуальные скрипты запуска
    create_java_scripts()
    create_frontend_scripts()
    create_ml_scripts()
    
    # Скрипт для разработки всего проекта
    create_file("start-dev.sh", """#!/bin/bash
echo "🎯 Starting all services in development mode..."
echo "💡 Run each service in separate terminals for better debugging"

echo ""
echo "📋 To start individually:"
echo "  ML Service:      cd ML && ./run-dev.sh"
echo "  Java Server:     cd JavaServer && ./run-dev.sh" 
echo "  Frontend:        cd frontend && ./run-dev.sh"
echo ""
echo "🌐 URLs when running:"
echo "  Frontend:    http://localhost:3000"
echo "  Java API:    http://localhost:8080"
echo "  ML Service:  http://localhost:5000"
""")
    
    make_executable("start-docker.sh")
    make_executable("start-dev.sh")

def create_java_scripts():
    """Create JavaServer scripts"""
    create_file("JavaServer/run-dev.sh", """#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting JavaServer in development mode..."

# Set development environment
export SPRING_PROFILES_ACTIVE=local
export ML_SERVICE_URL=http://localhost:5000

echo "Active profile: $SPRING_PROFILES_ACTIVE"
echo "ML Service URL: $ML_SERVICE_URL"

./gradlew bootRun
""")
    
    create_file("JavaServer/run-dev.bat", """@echo off
cd /d %~dp0
echo 🚀 Starting JavaServer in development mode...

set SPRING_PROFILES_ACTIVE=local
set ML_SERVICE_URL=http://localhost:5000

echo Active profile: %SPRING_PROFILES_ACTIVE%
echo ML Service URL: %ML_SERVICE_URL%

gradlew bootRun
pause
""")
    
    make_executable("JavaServer/run-dev.sh")

def create_frontend_scripts():
    """Create frontend scripts"""
    create_file("frontend/run-dev.sh", """#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting Frontend in development mode..."
npm run dev
""")
    
    create_file("frontend/run-dev.bat", """@echo off
cd /d %~dp0
echo 🚀 Starting Frontend in development mode...
npm run dev
pause
""")
    
    make_executable("frontend/run-dev.sh")

def create_ml_scripts():
    """Create ML service scripts"""
    create_file("ML/run-dev.sh", """#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting ML Service in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip

# Try to install from requirements, skip mediapipe if it fails
if pip install -r requirements.txt; then
    echo "✅ All dependencies installed successfully"
else
    echo "⚠️  Some dependencies failed, installing core packages..."
    pip install flask opencv-python numpy scipy scikit-image pillow requests
fi

echo "🌐 Starting ML service on http://localhost:5000"
python app.py
""")
    
    create_file("ML/run-dev.bat", """@echo off
cd /d %~dp0
echo 🚀 Starting ML Service in development mode...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment  
echo 🔧 Activating virtual environment...
call venv\\Scripts\\activate

REM Install requirements
echo 📥 Installing dependencies...
pip install --upgrade pip

REM Try to install requirements
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️  Some dependencies failed, installing core packages...
    pip install flask opencv-python numpy scipy scikit-image pillow requests
)

echo 🌐 Starting ML service on http://localhost:5000
python app.py
pause
""")
    
    make_executable("ML/run-dev.sh")

def create_env_files():
    """Create environment configuration files"""
    
    # Root .env.example
    create_file(".env.example", """# Project Environment Configuration
# Copy this file to .env and adjust values

# Database
POSTGRES_DB=healthpix
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Service URLs (Development)
JAVA_SERVER_URL=http://localhost:8080
ML_SERVICE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000

# Service URLs (Docker)
JAVA_SERVER_DOCKER_URL=http://java-server:8080
ML_SERVICE_DOCKER_URL=http://ml-service:5000

# Spring Profiles
SPRING_PROFILES_ACTIVE=local
""")
    
    # Frontend env
    create_file("frontend/.env", """# Frontend Development Configuration
VITE_API_BASE_URL=http://localhost:8080
""")
    
    create_file("frontend/.env.production", """# Frontend Production Configuration
VITE_API_BASE_URL=/api
""")

def fix_application_properties():
    """Fix JavaServer configuration files"""
    
    # Исправляем application.properties
    app_props = """# Base configuration - profile specific settings in application-{profile}.properties
spring.datasource.driver-class-name=org.postgresql.Driver
spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true

server.address=0.0.0.0
server.port=8080

# ML Service configuration
ai.ml.service.url=${ML_SERVICE_URL:http://localhost:5000}

# Activate profiles via SPRING_PROFILES_ACTIVE environment variable
# Available profiles: local, docker
"""
    
    create_file("JavaServer/src/main/resources/application.properties", app_props)
    
    # Локальная конфигурация для разработки
    local_props = """# Local Development Profile
# Uses local PostgreSQL instance

spring.datasource.url=jdbc:postgresql://localhost:5432/${POSTGRES_DB:healthpix}
spring.datasource.username=${POSTGRES_USER:postgres}
spring.datasource.password=${POSTGRES_PASSWORD:postgres}

# ML service for local development
ai.ml.service.url=http://localhost:5000

# Development settings
spring.jpa.show-sql=true
logging.level.aiapp=DEBUG
"""
    
    create_file("JavaServer/src/main/resources/application-local.properties", local_props)
    
    # Docker конфигурация
    docker_props = """# Docker Profile
# Uses Docker service names

spring.datasource.url=jdbc:postgresql://db:5432/${POSTGRES_DB:healthpix}
spring.datasource.username=${POSTGRES_USER:postgres}
spring.datasource.password=${POSTGRES_PASSWORD:postgres}

# ML service in Docker network
ai.ml.service.url=http://ml-service:5000

# Production settings
spring.jpa.show-sql=false
logging.level.aiapp=INFO
"""
    
    create_file("JavaServer/src/main/resources/application-docker.properties", docker_props)

def update_docker_compose():
    """Update docker-compose.yml with better configuration"""
    docker_compose = """version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-healthpix}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  java-server:
    build: ./JavaServer
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/${POSTGRES_DB:-healthpix}
      - SPRING_DATASOURCE_USERNAME=${POSTGRES_USER:-postgres}
      - SPRING_DATASOURCE_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - ML_SERVICE_URL=http://ml-service:5000
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  ml-service:
    build: ./ML
    ports:
      - "5000:5000"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - java-server
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
"""
    create_file("docker-compose.yml", docker_compose)

def main():
    print("🎯 Starting Project Refactoring...")
    print("=" * 50)
    
    # 1. Очистка проекта
    print("\n1. 🗑️  Cleaning up project...")
    cleanup_project()
    
    # 2. Создание .gitignore
    print("\n2. 📝 Creating .gitignore...")
    create_gitignore()
    
    # 3. Создание скриптов
    print("\n3. 🔧 Creating launch scripts...")
    create_scripts()
    
    # 4. Конфигурационные файлы
    print("\n4. ⚙️  Creating configuration files...")
    create_env_files()
    
    # 5. Исправление конфигов Java
    print("\n5. ☕ Fixing JavaServer configuration...")
    fix_application_properties()
    
    # 6. Обновление Docker Compose
    print("\n6. 🐳 Updating docker-compose.yml...")
    update_docker_compose()
    
    print("\n" + "=" * 50)
    print("✅ Refactoring completed!")
    print("\n📋 Next steps:")
    print("  1. Run: python refactor.py (this script)")
    print("  2. Copy .env.example to .env and adjust values")
    print("  3. For Docker: ./start-docker.sh")
    print("  4. For development: see start-dev.sh for individual service startup")
    print("\n🚀 Happy coding!")

if __name__ == "__main__":
    main()
