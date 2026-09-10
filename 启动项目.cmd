@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 JD Select...
echo 启动成功后，请打开 http://127.0.0.1:5173
echo API 文档：http://127.0.0.1:8000/docs
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1"
echo.
echo 服务已经停止或启动失败。请查看上方提示。
pause
