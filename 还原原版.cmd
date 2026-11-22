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

echo [1/2] 还原资源文件...
python "%HERE%patch_resource.py" --restore
if errorlevel 1 (
    echo [失败] 资源还原出错
    pause
    exit /b 1
)

echo.
echo [2/2] 还原左侧菜单...
python "%HERE%patch_menu.py" --restore
if errorlevel 1 (
    echo [失败] 菜单还原出错
    pause
    exit /b 1
)

echo.
echo 还原完成。
pause
