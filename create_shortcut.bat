@echo off
REM Windows 바로가기 생성 스크립트

set APP_NAME=CardReader
set APP_PATH=%~dp0dist\%APP_NAME%.exe
set DESKTOP_PATH=%USERPROFILE%\Desktop

if not exist "%APP_PATH%" (
    echo 앱을 먼저 빌드하세요: python build_installer.py
    exit /b 1
)

REM 바로가기 생성 (PowerShell 사용)
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_PATH%\%APP_NAME%.lnk'); $Shortcut.TargetPath = '%APP_PATH%'; $Shortcut.WorkingDirectory = '%~dp0dist'; $Shortcut.Save()"

echo 바로가기가 생성되었습니다: %DESKTOP_PATH%\%APP_NAME%.lnk

