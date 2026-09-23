@echo off
title Web Performance Check
cd /d "%~dp0"
echo Menjalankan check_performance_local.py...
echo ========================================
python check_performance_local.py
echo ========================================
echo Selesai.
pause

