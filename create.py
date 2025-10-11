#!/usr/bin/env python3
"""
Development Environment Setup Script
Automatically sets up infrastructure for developers based on their role
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None, shell=False):
    """Run shell command and return success status"""
    try:
        print(f"🛠️  Running: {cmd}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Success: {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {cmd}")
        print(f"Error: {e.stderr}")
        return False

def setup_frontend():
    """Setup and start frontend in dev mode"""
    print("\n🎨 Setting up Frontend...")

    # Install dependencies
    if not run_command(["npm", "install"], cwd="frontend"):
        return False

    print("✅ Frontend dependencies installed")
    print("💡 To start frontend manually: cd frontend && npm run dev")
    return True

def setup_java_server():
    """Setup Java server"""
    print("\n☕ Setting up Java Server...")

    # Build the project
    if not run_command(["./gradlew", "build", "-x", "test"], cwd="JavaServer"):
        return False

    print("✅ Java Server built successfully")
    print("💡 To start Java server manually: cd JavaServer && ./run-dev.sh")
    return True

def setup_ml_service():
    """Setup ML service"""
    print("\n🤖 Setting up ML Service...")

    # Create virtual environment if it doesn't exist
    if not os.path.exists("ML/venv"):
        print("Creating virtual environment...")
        if not run_command(["python", "-m", "venv", "venv"], cwd="ML"):
            return False

    # Install requirements
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    if not run_command([pip_cmd, "install", "-r", "requirements.txt"], cwd="ML"):
        print("⚠️  Some dependencies failed, installing core packages...")
        core_packages = ["flask", "opencv-python", "numpy", "scipy", "scikit-image", "pillow", "requests"]
        if not run_command([pip_cmd, "install"] + core_packages, cwd="ML"):
            return False

    print("✅ ML Service dependencies installed")
    print("💡 To start ML service manually: cd ML && ./run-dev.sh")
    return True

def update_frontend_bat_script():
    """Update frontend bat script to include npm install"""
    bat_content = """@echo off
cd /d %~dp0
echo 🚀 Starting Frontend in development mode...

REM Check and install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
)

echo ✅ Starting dev server...
npm run dev
pause
"""

    with open("frontend/run-dev.bat", "w", encoding='utf-8') as f:
        f.write(bat_content)
    print("✅ Updated frontend/run-dev.bat with npm install")

def create_dev_scripts():
    """Create development scripts for different roles"""

    # Script for Frontend developers (starts everything except frontend)
    frontend_dev_script = """#!/bin/bash
echo "🎯 Starting infrastructure for Frontend Developer..."
echo "📦 Starting database and backend services..."

docker-compose up db java-server ml-service

echo "💡 Now start frontend in your IDE: cd frontend && npm run dev"
"""

    # Script for Java developers (starts everything except java-server)
    java_dev_script = """#!/bin/bash
echo "🎯 Starting infrastructure for Java Developer..."
echo "📦 Starting database, ML service and frontend..."

docker-compose up db ml-service frontend

echo "💡 Now start Java server in your IDE: cd JavaServer && ./run-dev.sh"
"""

    # Script for ML developers (starts everything except ml-service)
    ml_dev_script = """#!/bin/bash
echo "🎯 Starting infrastructure for ML Developer..."
echo "📦 Starting database, Java server and frontend..."

docker-compose up db java-server frontend

echo "💡 Now start ML service in your IDE: cd ML && ./run-dev.sh"
"""

    scripts = {
        "start-for-frontend-dev.sh": frontend_dev_script,
        "start-for-java-dev.sh": java_dev_script,
        "start-for-ml-dev.sh": ml_dev_script
    }

    for filename, content in scripts.items():
        with open(filename, "w", encoding='utf-8') as f:
            f.write(content)
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(filename, 0o755)
        print(f"✅ Created {filename}")

def create_bat_scripts():
    """Create Windows batch scripts for different roles"""

    # Batch script for Frontend developers
    frontend_dev_bat = """@echo off
echo 🎯 Starting infrastructure for Frontend Developer...
echo 📦 Starting database and backend services...

docker-compose up db java-server ml-service

echo 💡 Now start frontend in your IDE: cd frontend && npm run dev
pause
"""

    # Batch script for Java developers
    java_dev_bat = """@echo off
echo 🎯 Starting infrastructure for Java Developer...
echo 📦 Starting database, ML service and frontend...

docker-compose up db ml-service frontend

echo 💡 Now start Java server in your IDE: cd JavaServer && run-dev.bat
pause
"""

    # Batch script for ML developers
    ml_dev_bat = """@echo off
echo 🎯 Starting infrastructure for ML Developer...
echo 📦 Starting database, Java server and frontend...

docker-compose up db java-server frontend

echo 💡 Now start ML service in your IDE: cd ML && run-dev.bat
pause
"""

    scripts = {
        "start-for-frontend-dev.bat": frontend_dev_bat,
        "start-for-java-dev.bat": java_dev_bat,
        "start-for-ml-dev.bat": ml_dev_bat
    }

    for filename, content in scripts.items():
        with open(filename, "w", encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created {filename}")

def main():
    parser = argparse.ArgumentParser(description="Setup development environment")
    parser.add_argument("--role", choices=["frontend", "java", "ml", "all"],
                       default="all", help="Developer role to setup for")
    parser.add_argument("--create-scripts", action="store_true",
                       help="Create role-specific startup scripts")

    args = parser.parse_args()

    print("🚀 Development Environment Setup")
    print("=" * 50)

    # Update frontend bat script with npm install
    update_frontend_bat_script()

    # Setup based on role
    if args.role in ["frontend", "all"]:
        setup_frontend()

    if args.role in ["java", "all"]:
        setup_java_server()

    if args.role in ["ml", "all"]:
        setup_ml_service()

    # Create role-specific scripts
    if args.create_scripts:
        print("\n📜 Creating role-specific startup scripts...")
        create_dev_scripts()
        create_bat_scripts()

    print("\n" + "=" * 50)
    print("✅ Setup completed!")

    # Show usage instructions
    print("\n🎯 Usage Instructions:")
    print("\nFor Frontend Developers:")
    print("  ./start-for-frontend-dev.sh  # Linux/Mac")
    print("  start-for-frontend-dev.bat   # Windows")
    print("  Then start frontend: cd frontend && npm run dev")

    print("\nFor Java Developers:")
    print("  ./start-for-java-dev.sh      # Linux/Mac")
    print("  start-for-java-dev.bat       # Windows")
    print("  Then start Java server: cd JavaServer && ./run-dev.sh")

    print("\nFor ML Developers:")
    print("  ./start-for-ml-dev.sh        # Linux/Mac")
    print("  start-for-ml-dev.bat         # Windows")
    print("  Then start ML service: cd ML && ./run-dev.sh")

    print("\n🌐 Services will be available at:")
    print("  Frontend:    http://localhost:3000")
    print("  Java API:    http://localhost:8080")
    print("  ML Service:  http://localhost:5000")
    print("  Database:    localhost:5432")

if __name__ == "__main__":
    main()
