@echo off
REM Windows health check script
echo Running Qualitative Coding Analysis Tool health check...
echo.

python scripts/validate_setup.py %*

echo.
echo For more information, see the detailed report in logs/
pause