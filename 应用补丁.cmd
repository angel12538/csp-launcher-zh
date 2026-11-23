@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   CLIP STUDIO 启动器 简体中文补丁
echo ==========================================
echo.
echo 本工具会把启动器的繁体中文界面转为简体，
echo 并把台湾用语本地化为大陆用语。
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

echo [1/4] 转换左侧菜单...
python "%HERE%patch_menu.py"
if errorlevel 1 (
    echo [失败] 菜单转换出错
    pause
    exit /b 1
)
echo.

echo [2/4] 转换页面语言表...
python "%HERE%patch_pagejs.py"
if errorlevel 1 (
    echo [失败] 页面语言表转换出错
    pause
    exit /b 1
)
echo.

echo [3/4] 转换主内容资源（繁 -> 简 + 台湾用语）...
python "%HERE%patch_resource.py"
if errorlevel 1 (
    echo [失败] 资源转换出错
    pause
    exit /b 1
)
echo.

echo [4/4] 本地化页面与菜单脚本里的台湾用语...
python "%HERE%patch_terms.py" --apply
if errorlevel 1 (
    echo [失败] 术语本地化出错
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   完成！请启动 CLIP STUDIO 查看效果
echo ==========================================
pause
