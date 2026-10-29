@echo off
title Wiki Agent System
cd /d "%~dp0"
call venv\Scripts\activate.bat
wiki-agent chat
pause