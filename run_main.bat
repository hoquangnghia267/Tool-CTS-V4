@echo off
Powershell -WindowStyle Hidden -Command "& {Start-Process python.exe -ArgumentList 'main.py' -NoNewWindow -Wait}"