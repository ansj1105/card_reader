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

def build_installer(app_type="both"):
    """
    인스톨러 빌드
    
    Args:
        app_type: "web", "desktop", "both" 중 하나
    """
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
    
    # 빌드할 애플리케이션 목록
    apps_to_build = []
    if app_type == "web" or app_type == "both":
        apps_to_build.append(("web", "card_reader_web.py", "CardReaderWeb"))
    if app_type == "desktop" or app_type == "both":
        apps_to_build.append(("desktop", "card_reader_desktop.py", "CardReaderDesktop"))
    
    for app_name, script_file, exe_name in apps_to_build:
        print(f"\n{'='*60}")
        print(f"{app_name.upper()} 애플리케이션 빌드 중...")
        print(f"{'='*60}\n")
        
        # 빌드 디렉토리 정리 (첫 번째 빌드만)
        if app_name == apps_to_build[0][0]:
            if os.path.exists("build"):
                shutil.rmtree("build")
            if os.path.exists("dist"):
                shutil.rmtree("dist")
        
        # spec 파일 정리
        spec_file = f"{exe_name}.spec"
        if os.path.exists(spec_file):
            os.remove(spec_file)
        
        # PyInstaller 명령 구성
        cmd = [
            "pyinstaller",
            f"--name={exe_name}",
            "--onefile",  # 단일 실행 파일로 생성 (Python 포함)
            "--noconsole" if system == "Windows" else "--windowed",  # 콘솔 창 숨김
            "--add-data=README.md:." if system != "Windows" else "--add-data=README.md;.",  # README 포함
            "--hidden-import=smartcard",
            "--hidden-import=smartcard.System",
            "--hidden-import=smartcard.scard",
            "--collect-all=smartcard",  # smartcard 패키지 전체 포함
        ]
        
        # 웹 애플리케이션인 경우 추가 옵션
        if app_name == "web":
            cmd.extend([
                "--hidden-import=uvicorn.lifespan.on",
                "--hidden-import=uvicorn.lifespan.off",
                "--hidden-import=uvicorn.protocols.websockets.auto",
                "--hidden-import=uvicorn.protocols.http.auto",
                "--hidden-import=uvicorn.loops.auto",
                "--hidden-import=uvicorn.logging",
            ])
        
        # 데스크톱 애플리케이션인 경우 PyQt5 관련 옵션
        if app_name == "desktop":
            cmd.extend([
                "--hidden-import=PyQt5",
                "--hidden-import=PyQt5.QtCore",
                "--hidden-import=PyQt5.QtGui",
                "--hidden-import=PyQt5.QtWidgets",
                "--collect-all=PyQt5",  # PyQt5 패키지 전체 포함
            ])
        
        cmd.append(script_file)
        
        if system == "Darwin":  # macOS
            cmd.extend([
                f"--osx-bundle-identifier=com.cardreader.{app_name}",
            ])
        
        # 빌드 실행
        print("빌드 명령 실행 중...")
        print(" ".join(cmd))
        print("\n빌드 중... (시간이 걸릴 수 있습니다)\n")
        subprocess.check_call(cmd)
        
        # 빌드 결과 출력
        print(f"\n{app_name.upper()} 빌드 완료!")
        if system == "Darwin":
            app_path = f"dist/{exe_name}.app"
            print(f"실행 파일 위치: {app_path}")
            print(f"실행 방법: open {app_path}")
        elif system == "Windows":
            exe_path = f"dist/{exe_name}.exe"
            print(f"실행 파일 위치: {exe_path}")
            print(f"실행 방법: {exe_path} 더블클릭")
        else:
            exe_path = f"dist/{exe_name}"
            print(f"실행 파일 위치: {exe_path}")
            print(f"실행 방법: ./{exe_path}")
    
    print("\n" + "="*60)
    print("전체 빌드 완료!")
    print("="*60)
    
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
    create_launcher(system, app_type)

def create_launcher(system, app_type="both"):
    """런처 스크립트 생성"""
    if system == "Darwin":
        # macOS .app 번들용 런처
        if app_type == "web" or app_type == "both":
            launcher_content = """#!/bin/bash
# 카드 리더기 웹 애플리케이션 런처
cd "$(dirname "$0")"
open CardReaderWeb.app
"""
            with open("dist/launch_web.sh", "w") as f:
                f.write(launcher_content)
            os.chmod("dist/launch_web.sh", 0o755)
        
        if app_type == "desktop" or app_type == "both":
            launcher_content = """#!/bin/bash
# 카드 리더기 데스크톱 애플리케이션 런처
cd "$(dirname "$0")"
open CardReaderDesktop.app
"""
            with open("dist/launch_desktop.sh", "w") as f:
                f.write(launcher_content)
            os.chmod("dist/launch_desktop.sh", 0o755)
        
    elif system == "Windows":
        # Windows 배치 파일
        if app_type == "web" or app_type == "both":
            launcher_content = """@echo off
cd /d "%~dp0"
start CardReaderWeb.exe
"""
            with open("dist/launch_web.bat", "w") as f:
                f.write(launcher_content)
        
        if app_type == "desktop" or app_type == "both":
            launcher_content = """@echo off
cd /d "%~dp0"
start CardReaderDesktop.exe
"""
            with open("dist/launch_desktop.bat", "w") as f:
                f.write(launcher_content)
        
    else:  # Linux
        if app_type == "web" or app_type == "both":
            launcher_content = """#!/bin/bash
cd "$(dirname "$0")"
./CardReaderWeb
"""
            with open("dist/launch_web.sh", "w") as f:
                f.write(launcher_content)
            os.chmod("dist/launch_web.sh", 0o755)
        
        if app_type == "desktop" or app_type == "both":
            launcher_content = """#!/bin/bash
cd "$(dirname "$0")"
./CardReaderDesktop
"""
            with open("dist/launch_desktop.sh", "w") as f:
                f.write(launcher_content)
            os.chmod("dist/launch_desktop.sh", 0o755)
    
    print("런처 스크립트 생성 완료")

if __name__ == "__main__":
    import sys
    # 명령줄 인자로 빌드 타입 지정 가능 (기본값: both)
    app_type = sys.argv[1] if len(sys.argv) > 1 else "both"
    if app_type not in ["web", "desktop", "both"]:
        print("사용법: python build_installer.py [web|desktop|both]")
        print("기본값: both (웹과 데스크톱 모두 빌드)")
        sys.exit(1)
    build_installer(app_type)

