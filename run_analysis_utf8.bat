@echo off
REM Set UTF-8 encoding for Windows console
chcp 65001 > nul

REM Run the analysis with UTF-8 encoding
python -u run_full_ai_analysis.py

REM Reset code page (optional)
REM chcp 437 > nul