#!/bin/bash
# macOS 바로가기 생성 스크립트 (웹 앱 + 데스크톱 앱)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_PATH="$HOME/Desktop"

# 웹 앱 바로가기
WEB_APP_NAME="CardReaderWeb"
WEB_APP_PATH="$SCRIPT_DIR/dist/${WEB_APP_NAME}.app"
WEB_SHORTCUT_PATH="$DESKTOP_PATH/${WEB_APP_NAME}.app"

# 데스크톱 앱 바로가기
DESKTOP_APP_NAME="CardReaderDesktop"
DESKTOP_APP_PATH="$SCRIPT_DIR/dist/${DESKTOP_APP_NAME}.app"
DESKTOP_SHORTCUT_PATH="$DESKTOP_PATH/${DESKTOP_APP_NAME}.app"

# 웹 앱 바로가기 생성
if [ -d "$WEB_APP_PATH" ]; then
    ln -sf "$WEB_APP_PATH" "$WEB_SHORTCUT_PATH"
    echo "✅ 웹 앱 바로가기 생성: $WEB_SHORTCUT_PATH"
else
    echo "⚠️  웹 앱을 찾을 수 없습니다. 먼저 빌드하세요: python build_installer.py web"
fi

# 데스크톱 앱 바로가기 생성
if [ -d "$DESKTOP_APP_PATH" ]; then
    ln -sf "$DESKTOP_APP_PATH" "$DESKTOP_SHORTCUT_PATH"
    echo "✅ 데스크톱 앱 바로가기 생성: $DESKTOP_SHORTCUT_PATH"
else
    echo "⚠️  데스크톱 앱을 찾을 수 없습니다. 먼저 빌드하세요: python build_installer.py desktop"
fi

echo ""
echo "바로가기 생성 완료!"
echo "- 웹 앱: $WEB_SHORTCUT_PATH"
echo "- 데스크톱 앱: $DESKTOP_SHORTCUT_PATH"

