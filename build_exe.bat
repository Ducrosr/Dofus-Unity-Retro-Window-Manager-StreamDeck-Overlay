@echo off
cd /d "%~dp0"
py -3.14 build_exe.py %*
pause
