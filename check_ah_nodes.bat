@echo off
chcp 65001 >nul
title Anhui Telecom IPTV Node Scanner
cd /d "%~dp0"
echo.
echo  ============================================================
echo   Anhui Telecom udpxy node scanner
echo  ============================================================
echo   Before running, make sure:
echo     1. You are on Anhui Telecom network (broadband or mobile hotspot)
echo     2. Proxy / VPN is OFF (including browser proxy extensions)
echo  ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo  [ERROR] Python 3 not found in PATH.
    echo  Please install Python 3 from python.org
    echo  and CHECK "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
  )
  set PY=py
) else (
  set PY=python
)

echo  Python found. Starting scan (about 2-5 minutes)...
echo  Scanning all archived network segments for live udpxy nodes.
echo.
%PY% scan_ah_ips.py
echo.
echo  ============================================================
echo   Scan finished. Results saved in the "ip" folder:
echo     - 检测报告_安徽电信.txt  (ranked report)
echo     - 可用节点_安徽电信.txt  (plain node list)
echo  ============================================================
echo.
pause
