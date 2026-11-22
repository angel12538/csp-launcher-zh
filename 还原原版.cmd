@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo   CLIP STUDIO 启动器 还原原版
echo ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 python。
    pause
    exit /b 1
)

taskkill /IM CLIPStudio.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

set HERE=%~dp0

echo [1/3] 还原左侧菜单...
python "%HERE%patch_menu.py" --restore
echo.
echo [2/3] 还原页面语言表...
python "%HERE%patch_pagejs.py" --restore
echo.
echo [3/3] 还原主内容资源...
python "%HERE%patch_resource.py" --restore

echo.
echo 还原完成。
pause
