#!/bin/bash
# 웹 GUI 프로그램 실행 스크립트
# 가상환경을 자동으로 생성하고 사용

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Python3 경로 찾기
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Python3를 찾을 수 없습니다."
    exit 1
fi

# 가상환경이 없으면 생성
if [ ! -d "$VENV_DIR" ]; then
    echo "가상환경을 생성하는 중..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo "가상환경 생성 실패. 시스템 Python에 패키지를 설치하시겠습니까? (y/n)"
        read -r answer
        if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
            echo "패키지 설치 중..."
            $PYTHON_CMD -m pip install --user -r "$SCRIPT_DIR/requirements.txt"
            $PYTHON_CMD "$SCRIPT_DIR/card_reader_web.py"
            exit $?
        else
            exit 1
        fi
    fi
fi

# 가상환경 활성화
source "$VENV_DIR/bin/activate"

# 패키지 설치 확인 및 설치
echo "필요한 패키지를 설치하는 중..."
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# pyscard 설치 확인
if ! python -c "from smartcard.System import readers" 2>/dev/null; then
    echo "⚠️  pyscard 설치에 문제가 있습니다. 웹 GUI는 실행되지만 카드 읽기 기능은 작동하지 않을 수 있습니다."
fi

# 웹 서버 실행
echo ""
echo "웹 서버 시작 중..."
echo "브라우저에서 http://localhost:8000 을 열어주세요"
echo ""
python "$SCRIPT_DIR/card_reader_web.py"

