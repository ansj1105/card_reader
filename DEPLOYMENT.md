# 배포 가이드

다른 환경(컴퓨터)에서 카드 리더기 프로그램을 실행하는 방법입니다.

## 배포 방법

### 1단계: 실행 파일 빌드

**중요:** 실행 파일은 빌드하는 운영체제와 동일한 OS에서만 작동합니다.
- macOS에서 빌드 → macOS용 `.app` 파일 생성
- Windows에서 빌드 → Windows용 `.exe` 파일 생성
- Linux에서 빌드 → Linux용 실행 파일 생성

#### macOS/Linux에서 빌드:
```bash
# 웹 앱과 데스크톱 앱 모두 빌드
python build_installer.py

# 또는 개별 빌드
python build_installer.py web      # 웹 앱만
python build_installer.py desktop  # 데스크톱 앱만
```

#### Windows에서 빌드:
```batch
# build_windows.bat 실행 (더블클릭 또는 명령 프롬프트에서)
build_windows.bat

# 또는 Python으로 직접 실행
python build_installer.py
```

빌드가 완료되면 `dist/` 폴더에 실행 파일이 생성됩니다.

### 2단계: 배포할 파일 준비

**macOS:**
- `dist/CardReaderWeb.app` - 웹 애플리케이션 (폴더 전체)
- `dist/CardReaderDesktop.app` - 데스크톱 애플리케이션 (폴더 전체)
- `dist/launch_web.sh` (선택사항) - 웹 앱 런처
- `dist/launch_desktop.sh` (선택사항) - 데스크톱 앱 런처

**Windows:**
- `dist/CardReaderWeb.exe` - 웹 애플리케이션 (단일 파일)
- `dist/CardReaderDesktop.exe` - 데스크톱 애플리케이션 (단일 파일)
- `dist/launch_web.bat` (선택사항) - 웹 앱 런처
- `dist/launch_desktop.bat` (선택사항) - 데스크톱 앱 런처

**Linux:**
- `dist/CardReaderWeb` - 웹 애플리케이션 (실행 파일)
- `dist/CardReaderDesktop` - 데스크톱 애플리케이션 (실행 파일)
- `dist/launch_web.sh` (선택사항) - 웹 앱 런처
- `dist/launch_desktop.sh` (선택사항) - 데스크톱 앱 런처

**참고:** Windows용 exe 파일을 만들려면 **Windows 컴퓨터에서 빌드**해야 합니다.

### 3단계: 대상 컴퓨터로 파일 전송

**방법 1: USB 드라이브 사용**
1. `dist/` 폴더의 실행 파일들을 USB 드라이브에 복사
2. 대상 컴퓨터로 USB 드라이브를 옮김
3. 실행 파일을 원하는 위치에 복사

**방법 2: 네트워크 전송**
- FTP, SCP, 공유 폴더 등을 사용하여 전송

**방법 3: 압축 파일로 전송**
```bash
# macOS/Linux
cd dist
zip -r CardReader.zip CardReaderWeb.app CardReaderDesktop.app launch_*.sh

# Windows
# dist 폴더를 우클릭 → 보내기 → 압축(ZIP) 폴더
# 또는 PowerShell에서:
# Compress-Archive -Path dist\*.exe,dist\*.bat -DestinationPath CardReader.zip
```

**Windows용 빌드가 필요한 경우:**
1. Windows 컴퓨터에서 이 프로젝트를 다운로드
2. `build_windows.bat` 파일을 더블클릭하여 실행
3. 빌드 완료 후 `dist/` 폴더의 `.exe` 파일들을 배포

### 4단계: 대상 컴퓨터에서 PC/SC 라이브러리 설치

**중요:** 실행 파일만으로는 작동하지 않습니다. PC/SC 라이브러리를 별도로 설치해야 합니다.

#### macOS
```bash
brew install pcsc-lite
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install pcscd libpcsclite-dev
sudo systemctl start pcscd
sudo systemctl enable pcscd
```

#### Linux (RedHat/CentOS)
```bash
sudo yum install pcsc-lite pcsc-lite-devel
sudo systemctl start pcscd
sudo systemctl enable pcscd
```

#### Windows
Windows는 PC/SC가 기본 제공되므로 추가 설치가 필요 없습니다.

### 5단계: 실행

#### macOS
```bash
# 웹 앱 실행
open CardReaderWeb.app

# 데스크톱 앱 실행
open CardReaderDesktop.app
```

#### Windows
- `CardReaderWeb.exe` 더블클릭
- `CardReaderDesktop.exe` 더블클릭

#### Linux
```bash
# 실행 권한 부여
chmod +x CardReaderWeb CardReaderDesktop

# 웹 앱 실행
./CardReaderWeb

# 데스크톱 앱 실행
./CardReaderDesktop
```

## 배포 체크리스트

- [ ] 실행 파일 빌드 완료 (`python build_installer.py`)
- [ ] `dist/` 폴더의 실행 파일 확인
- [ ] 대상 컴퓨터로 파일 전송
- [ ] 대상 컴퓨터에 PC/SC 라이브러리 설치
- [ ] 카드 리더기 연결 확인
- [ ] 프로그램 실행 테스트

## 문제 해결

### "PC/SC 라이브러리를 사용할 수 없습니다" 오류
→ PC/SC 라이브러리가 설치되지 않았습니다. 위의 4단계를 참고하여 설치하세요.

### "리더기 연결 실패" 오류
→ 다음을 확인하세요:
- 카드 리더기가 USB에 연결되어 있는지
- 다른 프로그램에서 리더기를 사용 중이 아닌지
- PC/SC 라이브러리가 제대로 설치되었는지

### 실행 파일이 실행되지 않음
→ 실행 권한을 확인하세요:
```bash
chmod +x CardReaderWeb CardReaderDesktop
```

## 최소 배포 패키지

다른 환경에서 실행하기 위해 필요한 최소 파일:

**macOS:**
- `CardReaderWeb.app` 또는 `CardReaderDesktop.app` (하나만 선택해도 됨)
- PC/SC 라이브러리 설치 필요

**Windows:**
- `CardReaderWeb.exe` 또는 `CardReaderDesktop.exe` (하나만 선택해도 됨)
- PC/SC는 기본 제공

**Linux:**
- `CardReaderWeb` 또는 `CardReaderDesktop` (하나만 선택해도 됨)
- PC/SC 라이브러리 설치 필요

**참고:** 실행 파일은 Python과 모든 의존성을 포함하고 있어 Python 설치 없이도 실행 가능합니다.

