#!/bin/bash
# macOS 바로가기 생성 스크립트

APP_NAME="CardReader"
APP_PATH="$(cd "$(dirname "$0")" && pwd)/dist/${APP_NAME}.app"
DESKTOP_PATH="$HOME/Desktop"

if [ ! -d "$APP_PATH" ]; then
    echo "앱을 먼저 빌드하세요: python build_installer.py"
    exit 1
fi

# 데스크톱에 바로가기 생성
ln -sf "$APP_PATH" "$DESKTOP_PATH/${APP_NAME}.app"

echo "바로가기가 생성되었습니다: $DESKTOP_PATH/${APP_NAME}.app"

