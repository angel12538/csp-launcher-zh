@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo   CLIP STUDIO PAINT 繁体转简体
echo ==========================================
echo.

echo 请先阅读 PAINT_PATCH_RISKS.md !
echo.
echo 本补丁会修改 CLIPStudioPaint.exe，仅验证于 1.11.6。
echo.
choice /C YN /M "确认已阅读风险说明并继续"
if errorlevel 2 exit /b 0
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 python。
    pause
    exit /b 1
)

taskkill /IM CLIPStudioPaint.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

set HERE=%~dp0

echo [1/2] 检查文件与版本...
python "%HERE%patch_paint.py" --check
echo.

choice /C YN /M "是否同时应用区域锁绕过（不加则可能出现锁区提示）"
if errorlevel 2 (
    python "%HERE%patch_paint.py" --apply
) else (
    python "%HERE%patch_paint.py" --apply --allow-region-bypass
)

echo.
pause
