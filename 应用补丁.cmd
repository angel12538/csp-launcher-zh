@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   CLIP STUDIO 启动器 简体中文补丁
echo ==========================================
echo.
echo 本工具会把启动器的繁体中文界面转为简体。
echo 需要 Python 3.9 及以上版本。
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 python，请先安装 Python 3 并加入 PATH。
    pause
    exit /b 1
)

taskkill /IM CLIPStudio.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

set HERE=%~dp0

echo [1/2] 转换资源文件...
python "%HERE%patch_resource.py"
if errorlevel 1 (
    echo [失败] 资源转换出错
    pause
    exit /b 1
)

echo.
echo [2/2] 转换左侧菜单...
python "%HERE%patch_menu.py"
if errorlevel 1 (
    echo [失败] 菜单转换出错
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   完成！请启动 CLIP STUDIO 查看效果
echo ==========================================
pause
