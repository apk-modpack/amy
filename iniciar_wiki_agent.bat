@echo off
title Wiki-Memory Agent — Modo Local
cd /d "%~dp0"
call venv\Scripts\activate.bat

echo.
echo  ============================================
echo   Wiki-Memory Agent — Modo Local (teclado)
echo  ============================================
echo.
echo  Para usar con la Sala de Chat grafica:
echo    1. iniciar_sala_de_chat.bat
echo    2. iniciar_agente_modo_red.bat
echo.

wiki-agent chat
pause
