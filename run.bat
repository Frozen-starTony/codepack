@echo off
python "%~dp0codepack.py" %*
if errorlevel 1 pause
