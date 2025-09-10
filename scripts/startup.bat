@echo off
echo === Qualitative Coding System Startup ===
echo.

REM 1. Check Docker
echo Step 1: Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)
echo √ Docker is installed

REM 2. Start Neo4j
echo.
echo Step 2: Starting Neo4j...
docker-compose up -d
timeout /t 5 >nul

REM 3. Verify Neo4j is running
echo.
echo Step 3: Verifying Neo4j connection...
curl -s http://localhost:7474 >nul 2>&1
if %errorlevel% equ 0 (
    echo √ Neo4j is running on port 7474
) else (
    echo ERROR: Neo4j is not accessible
    echo Check docker logs: docker logs qualitative_coding_neo4j_1
    pause
    exit /b 1
)

REM 4. Check environment
echo.
echo Step 4: Checking environment...
if exist .env (
    echo √ .env file exists
    findstr /C:"GEMINI_API_KEY" .env >nul
    if %errorlevel% equ 0 (
        echo √ Gemini API key configured
    ) else (
        echo WARNING: Gemini API key not found in .env
    )
) else (
    echo ERROR: .env file not found
    echo Copy .env.example to .env and add your API keys
    pause
    exit /b 1
)

REM 5. Run quick validation
echo.
echo Step 5: Running quick validation tests...
python -m pytest tests/test_fail_fast_validation.py -q

echo.
echo === System Ready ===
echo.
echo To run full test suite:
echo   python -m pytest tests/ -v
echo.
echo To analyze an interview:
echo   python -m qc.cli analyze sample_interview.txt
echo.
echo To stop Neo4j:
echo   docker-compose down
echo.
pause