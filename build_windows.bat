@echo off
REM Windows용 빌드 스크립트
REM PyInstaller를 사용하여 Windows 실행 파일 생성

echo Windows용 카드 리더기 프로그램 빌드 시작...
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo 오류: Python이 설치되어 있지 않습니다.
    echo Python을 설치한 후 다시 시도하세요.
    pause
    exit /b 1
)

REM 가상환경 확인 및 생성
if not exist "venv" (
    echo 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip --quiet

REM 필요한 패키지 설치
echo 필요한 패키지를 설치하는 중...
pip install -r requirements.txt --quiet

REM PyInstaller 설치 확인
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller --quiet
)

REM 빌드 디렉토리 정리
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "CardReaderWeb.spec" del /q CardReaderWeb.spec
if exist "CardReaderDesktop.spec" del /q CardReaderDesktop.spec

echo.
echo ========================================
echo 웹 애플리케이션 빌드 중...
echo ========================================
echo.

REM 웹 앱 빌드
pyinstaller --name=CardReaderWeb ^
    --onefile ^
    --noconsole ^
    --add-data=README.md;. ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=uvicorn.lifespan.off ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=smartcard ^
    --hidden-import=smartcard.System ^
    --hidden-import=smartcard.scard ^
    --collect-all=smartcard ^
    card_reader_web.py

if errorlevel 1 (
    echo 웹 앱 빌드 실패!
    pause
    exit /b 1
)

echo.
echo ========================================
echo 데스크톱 애플리케이션 빌드 중...
echo ========================================
echo.

REM 데스크톱 앱 빌드
pyinstaller --name=CardReaderDesktop ^
    --onefile ^
    --noconsole ^
    --add-data=README.md;. ^
    --hidden-import=smartcard ^
    --hidden-import=smartcard.System ^
    --hidden-import=smartcard.scard ^
    --collect-all=smartcard ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --collect-all=PyQt5 ^
    card_reader_desktop.py

if errorlevel 1 (
    echo 데스크톱 앱 빌드 실패!
    pause
    exit /b 1
)

REM 런처 배치 파일 생성
echo.
echo 런처 파일 생성 중...

REM 웹 앱 런처
(
echo @echo off
echo cd /d "%%~dp0"
echo start CardReaderWeb.exe
) > dist\launch_web.bat

REM 데스크톱 앱 런처
(
echo @echo off
echo cd /d "%%~dp0"
echo start CardReaderDesktop.exe
) > dist\launch_desktop.bat

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo 실행 파일 위치:
echo   - 웹 앱: dist\CardReaderWeb.exe
echo   - 데스크톱 앱: dist\CardReaderDesktop.exe
echo.
echo 배포 방법:
echo   1. dist 폴더의 .exe 파일들을 다른 컴퓨터로 복사
echo   2. Windows는 PC/SC가 기본 제공되므로 추가 설치 불필요
echo   3. .exe 파일을 더블클릭하여 실행
echo.
pause

