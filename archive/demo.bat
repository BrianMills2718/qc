@echo off
REM One-Click Demo Launcher for Windows
REM Launch the qualitative coding analysis tool with pre-loaded AI research data

echo 🚀 Qualitative Coding Analysis Tool - One-Click Demo
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed
    echo 💡 Please install Python 3.8+ from python.org and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ❌ Please run this script from the qualitative-coding root directory
    echo 💡 Expected structure: src\qc\, requirements.txt, etc.
    pause
    exit /b 1
)

if not exist "src\qc" (
    echo ❌ Please run this script from the qualitative-coding root directory
    echo 💡 Expected structure: src\qc\, requirements.txt, etc.
    pause
    exit /b 1
)

echo ✅ Environment check passed
echo.

REM Ask user preference
echo Choose demo launch method:
echo 1) Docker (recommended - isolated environment)
echo 2) Local Python (direct installation)
echo 3) Quick Docker Hub pull (fastest)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo 🐳 Launching with Docker...
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Docker Compose is required but not installed
        echo 💡 Please install Docker Desktop for Windows
        pause
        exit /b 1
    )
    
    docker-compose -f config\docker\docker-compose.demo.yml up --build
) else if "%choice%"=="2" (
    echo 🐍 Launching with local Python...
    python scripts\launch_demo.py
) else if "%choice%"=="3" (
    echo ⚡ Quick Docker Hub launch...
    echo 🚧 Docker Hub image coming soon - using local Docker for now
    docker-compose -f config\docker\docker-compose.demo.yml up --build
) else (
    echo ❌ Invalid choice. Please run again and choose 1, 2, or 3.
    pause
    exit /b 1
)

pause