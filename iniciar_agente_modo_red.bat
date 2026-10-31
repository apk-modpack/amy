@echo off
title Wiki-Memory Agent — Modo Red
cd /d "%~dp0"
call venv\Scripts\activate.bat

echo.
echo  ============================================
echo   Wiki-Memory Agent — Modo Red
echo  ============================================
echo.
echo  Asegurate de que la Sala de Chat ya esta
echo  iniciada antes de continuar.
echo.

wiki-agent chat
pause

