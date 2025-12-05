#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카드 리더기 프로그램 인스톨러 빌드 스크립트
PyInstaller를 사용하여 실행 파일 생성
"""

import os
import sys
import subprocess
import shutil
import platform

def build_installer():
    """인스톨러 빌드"""
    system = platform.system()
    
    print(f"시스템: {system}")
    print("인스톨러 빌드 시작...")
    print("주의: Python과 모든 의존성이 실행 파일에 포함됩니다.")
    print("      다른 컴퓨터에서 Python 설치 없이 실행 가능합니다.\n")
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
        print("PyInstaller 확인됨")
    except ImportError:
        print("PyInstaller 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 빌드 디렉토리 정리
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists(f"CardReader.spec"):
        os.remove("CardReader.spec")
    
    # PyInstaller 명령 구성
    cmd = [
        "pyinstaller",
        "--name=CardReader",
        "--onefile",  # 단일 실행 파일로 생성 (Python 포함)
        "--noconsole" if system == "Windows" else "--windowed",  # 콘솔 창 숨김
        "--add-data=README.md:." if system != "Windows" else "--add-data=README.md;.",  # README 포함
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=smartcard",
        "--hidden-import=smartcard.System",
        "--hidden-import=smartcard.scard",
        "--collect-all=smartcard",  # smartcard 패키지 전체 포함
        "card_reader_web.py"
    ]
    
    if system == "Darwin":  # macOS
        cmd.extend([
            "--osx-bundle-identifier=com.cardreader.app",
        ])
    
    # 빌드 실행
    print("빌드 명령 실행 중...")
    print(" ".join(cmd))
    print("\n빌드 중... (시간이 걸릴 수 있습니다)\n")
    subprocess.check_call(cmd)
    
    print("\n" + "="*60)
    print("빌드 완료!")
    print("="*60)
    
    if system == "Darwin":
        app_path = "dist/CardReader.app"
        print(f"실행 파일 위치: {app_path}")
        print(f"실행 방법: open {app_path}")
    elif system == "Windows":
        exe_path = "dist/CardReader.exe"
        print(f"실행 파일 위치: {exe_path}")
        print(f"실행 방법: {exe_path} 더블클릭")
    else:
        exe_path = "dist/CardReader"
        print(f"실행 파일 위치: {exe_path}")
        print(f"실행 방법: ./{exe_path}")
    
    print("\n중요:")
    print("- 실행 파일은 Python이 포함되어 있어 Python 설치 없이 실행 가능합니다.")
    print("- 하지만 PC/SC 라이브러리는 대상 컴퓨터에 별도로 설치해야 합니다:")
    if system == "Darwin":
        print("  macOS: brew install pcsc-lite")
    elif system == "Linux":
        print("  Linux: sudo apt-get install pcscd libpcsclite-dev")
    else:
        print("  Windows: 기본 제공 (추가 설치 불필요)")
    
    # 런처 스크립트 생성
    create_launcher(system)

def create_launcher(system):
    """런처 스크립트 생성"""
    if system == "Darwin":
        # macOS .app 번들용 런처
        launcher_content = """#!/bin/bash
# 카드 리더기 런처
cd "$(dirname "$0")"
./CardReader.app/Contents/MacOS/CardReader
"""
        with open("dist/launch.sh", "w") as f:
            f.write(launcher_content)
        os.chmod("dist/launch.sh", 0o755)
        
    elif system == "Windows":
        # Windows 배치 파일
        launcher_content = """@echo off
cd /d "%~dp0"
start CardReader.exe
"""
        with open("dist/launch.bat", "w") as f:
            f.write(launcher_content)
        
    else:  # Linux
        launcher_content = """#!/bin/bash
cd "$(dirname "$0")"
./CardReader
"""
        with open("dist/launch.sh", "w") as f:
            f.write(launcher_content)
        os.chmod("dist/launch.sh", 0o755)
    
    print("런처 스크립트 생성 완료")

if __name__ == "__main__":
    build_installer()

