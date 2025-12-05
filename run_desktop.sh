#!/bin/bash
# 카드 리더기 데스크톱 애플리케이션 실행 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "카드 리더기 데스크톱 애플리케이션 시작..."

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "가상환경을 생성하는 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
echo "pip 업그레이드 중..."
pip install --upgrade pip --quiet

# 필요한 패키지 설치
echo "필요한 패키지를 설치하는 중..."
pip install -r requirements.txt --quiet

# pyscard 설치 확인
if ! python -c "import smartcard" 2>/dev/null; then
    echo "pyscard 설치 중..."
    pip install pyscard --quiet
fi

# pyautogui 설치 확인
if ! python -c "import pyautogui" 2>/dev/null; then
    echo "pyautogui 설치 중..."
    pip install pyautogui --quiet
fi

# PC/SC 라이브러리 확인
if ! brew list pcsc-lite &>/dev/null 2>&1; then
    echo "⚠️  PC/SC 라이브러리가 설치되지 않았습니다."
    echo "다음 명령으로 설치하세요: brew install pcsc-lite"
    echo ""
    echo "계속 진행합니다 (카드 읽기 기능은 작동하지 않을 수 있습니다)..."
fi

# 데스크톱 애플리케이션 실행
echo "데스크톱 애플리케이션 실행 중..."
python "$SCRIPT_DIR/card_reader_desktop.py"

