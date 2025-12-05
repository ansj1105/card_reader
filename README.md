# ISO/IEC 14443 Type A/B 카드 리더기 프로그램

## 개요

본 프로그램은 ISO/IEC 14443 Type A/B 기반 비접촉식 카드를 지원하는 카드리더기를 통해 카드 번호를 읽어와 클립보드에 복사하는 기능을 제공합니다.

## 기능

- 카드 리더기 자동 감지 및 연결
- SELECT APDU를 이용한 카드 응용 선택
- 카드번호(고유식별번호) 읽기
- 클립보드 자동 복사
- **전체 화면 자동 입력** (데스크톱 애플리케이션)
  - 다른 애플리케이션의 입력 필드에 자동으로 카드번호 입력
  - 키보드 입력 시뮬레이션 (Ctrl+V / Cmd+V)

## 요구사항

- Python 3.7 이상
- ISO/IEC 14443 Type A/B 지원 카드 리더기 (예: ACR122)
- PC/SC 호환 드라이버 설치 필요

## 설치

### 방법 1: 실행 파일로 설치 (권장 - 다른 환경에서 사용)

**Python 설치 없이 실행 파일로 사용할 수 있습니다!**

1. **인스톨러 빌드:**
   ```bash
   python build_installer.py
   ```
   이 명령은 PyInstaller를 사용하여 Python과 모든 의존성을 포함한 단일 실행 파일을 생성합니다.

2. **바로가기 생성:**
   - macOS: `chmod +x create_shortcut.sh && ./create_shortcut.sh`
   - Windows: `create_shortcut.bat`

3. **배포:**
   - `dist/` 폴더의 실행 파일을 다른 컴퓨터로 복사
     - **macOS:** `CardReaderWeb.app`, `CardReaderDesktop.app`
     - **Windows:** `CardReaderWeb.exe`, `CardReaderDesktop.exe`
     - **Linux:** `CardReaderWeb`, `CardReaderDesktop`
   - **중요:** PC/SC 라이브러리는 대상 컴퓨터에 별도로 설치해야 합니다:
     - macOS: `brew install pcsc-lite`
     - Linux: `sudo apt-get install pcscd libpcsclite-dev`
     - Windows: 기본 제공 (추가 설치 불필요)
   - 실행 파일을 더블클릭하여 실행
   - **자세한 배포 가이드는 `DEPLOYMENT.md` 파일을 참고하세요.**

**참고:** 실행 파일은 Python이 포함되어 있어 Python 설치 없이도 작동합니다. 다만 PC/SC 라이브러리는 시스템 레벨에서 설치되어 있어야 합니다.

### 방법 2: 데스크톱 애플리케이션 실행 (권장 - 전체 화면 자동 입력)

**전체 화면에서 모든 입력 필드에 자동으로 카드번호를 입력할 수 있습니다!**

```bash
./run_desktop.sh
```

이 애플리케이션은:
- Tkinter 기반 GUI 제공
- 다른 애플리케이션(브라우저, 텍스트 에디터 등)의 입력 필드에 자동 입력
- 키보드 입력 시뮬레이션 (Ctrl+V / Cmd+V)
- 자동 읽기 및 자동 입력 옵션

**사용 방법:**
1. 프로그램 실행: `./run_desktop.sh`
2. "리더기 연결" 버튼 클릭
3. "자동 입력 (전체 화면)" 옵션 활성화 (기본값: 활성화)
4. 다른 애플리케이션의 입력 필드에 포커스
5. 카드를 리더기에 올리면 자동으로 입력됨

### 방법 3: 웹 애플리케이션 실행

웹 브라우저 기반 인터페이스 (같은 페이지의 입력 필드에만 자동 입력 가능):

```bash
./run_gui.sh
```

### 방법 4: 실행 스크립트 사용 (개발용)

실행 스크립트가 자동으로 가상환경을 생성하고 패키지를 설치합니다:

```bash
chmod +x run_gui.sh
./run_gui.sh
```

### 방법 3: Python 패키지로 설치

```bash
pip install -e .
card-reader  # 명령어로 실행
```

### 방법 4: 수동 설치

1. 가상환경 생성 (선택사항, 권장):

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

2. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```

3. PC/SC 라이브러리 설치:

### macOS
```bash
brew install pcsc-lite
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install pcscd libpcsclite-dev
```

### Windows
Windows는 PC/SC가 기본 제공되므로 추가 설치가 필요 없습니다.

## 사용 방법

### 웹 GUI 버전 (권장)

1. 웹 서버 실행:

```bash
chmod +x run_gui.sh
./run_gui.sh
```

또는 직접 실행:

```bash
source venv/bin/activate  # 가상환경 활성화
python card_reader_web.py
```

2. 브라우저에서 `http://localhost:8000` 열기

3. 웹 인터페이스에서:
   - "리더기 연결" 버튼 클릭
   - 카드를 리더기에 올려놓기
   - "카드 읽기" 버튼 클릭 또는 "자동 읽기" 체크박스 활성화
   - 읽은 카드번호가 자동으로 클립보드에 복사됨

**장점:**
- tkinter 호환성 문제 없음
- 모든 운영체제에서 동일하게 작동
- 모던한 웹 인터페이스
- 모바일 브라우저에서도 사용 가능

### 콘솔 버전

1. 카드 리더기를 컴퓨터에 연결
2. 카드를 리더기에 올려놓기
3. 프로그램 실행:

```bash
python card_reader.py
```

4. 프로그램이 자동으로:
   - 카드 리더기 연결
   - 카드 감지
   - SELECT APDU 전송
   - 카드번호 조회
   - 카드번호 추출
   - 클립보드에 복사

## APDU 명령

### SELECT APDU
```
00 A4 00 00 02 42 00
```
- 카드 응용 선택 명령

### 카드번호 조회 APDU
```
90 4C 00 00 04
```
- 카드번호 조회 명령

## 프로젝트 구조

```
card_reader/
├── card_reader.py      # 콘솔 버전 메인 프로그램
├── card_reader_web.py  # 웹 GUI 버전 메인 프로그램 (권장)
├── test_card_reader.py # 테스트 코드
├── run_gui.sh         # 웹 서버 실행 스크립트
├── build_installer.py # 인스톨러 빌드 스크립트
├── setup.py           # Python 패키지 설치 스크립트
├── create_shortcut.sh # macOS 바로가기 생성
├── create_shortcut.bat # Windows 바로가기 생성
├── requirements.txt    # Python 패키지 의존성
└── README.md          # 사용 설명서
```

## 주요 클래스 및 메서드

### CardReader 클래스

- `connect_to_reader()`: 카드 리더기에 연결
- `disconnect()`: 카드 리더기 연결 해제
- `check_card_presence()`: 카드 존재 여부 확인
- `select_card()`: SELECT APDU로 카드 선택
- `request_card_number()`: 카드번호 조회 요청
- `extract_card_number()`: 응답 데이터에서 카드번호 추출
- `copy_to_clipboard()`: 클립보드에 복사

### CardReaderGUI 클래스

- GUI 기반 카드 리더기 인터페이스
- 실시간 로그 표시
- 자동 읽기 모드 지원
- 스레드 기반 비동기 처리

## 로그

프로그램 실행 시 상세한 로그가 출력됩니다:
- 카드 리더기 연결 상태
- APDU 명령 전송 및 응답
- 카드번호 추출 과정
- 오류 메시지

## 문제 해결

## 설치 및 배포

### 방법 1: 실행 파일로 설치 (권장)

다른 환경에서 Python 설치 없이 사용할 수 있습니다.

1. **인스톨러 빌드:**
   ```bash
   python build_installer.py
   ```

2. **바로가기 생성:**
   - macOS: `./create_shortcut.sh`
   - Windows: `create_shortcut.bat`

3. **배포:**
   - `dist/` 폴더의 실행 파일을 다른 컴퓨터로 복사
   - 바로가기를 더블클릭하여 실행

### 방법 2: Python 패키지로 설치

```bash
pip install -e .
card-reader  # 명령어로 실행
```

### 방법 3: 개발 모드 실행

```bash
./run_gui.sh
```

### PC/SC 라이브러리를 사용할 수 없습니다

웹 인터페이스에서 "PC/SC 지원 안됨" 메시지가 표시되는 경우:

**해결 방법:**

1. **자동 설치 스크립트 사용 (권장)**
   ```bash
   ./install_pcsc.sh
   ```
   이 스크립트가 PC/SC 라이브러리를 자동으로 설치하고 pyscard를 재설치합니다.

2. **수동 설치 (macOS)**
   ```bash
   brew install pcsc-lite
   brew services start pcsc-lite
   rm -rf venv
   ./run_gui.sh
   ```

3. **수동 설치 (Linux)**
   ```bash
   sudo apt-get install pcscd libpcsclite-dev
   sudo systemctl start pcscd
   rm -rf venv
   ./run_gui.sh
   ```

**참고:** PC/SC 라이브러리가 없어도 웹 GUI는 실행됩니다. 다만 카드 읽기 기능은 작동하지 않습니다.

### 카드 리더기를 찾을 수 없습니다
- 카드 리더기가 올바르게 연결되었는지 확인
- PC/SC 드라이버가 설치되어 있는지 확인
- 리더기 제조사 드라이버 설치 필요 여부 확인

### 카드가 감지되지 않습니다
- 카드가 리더기 안테나 영역에 올바르게 위치했는지 확인
- 카드가 ISO/IEC 14443 Type A/B 호환인지 확인

### APDU 명령 실패
- 카드 타입에 따라 APDU 명령이 다를 수 있음
- 카드 제조사 문서를 참조하여 올바른 AID 및 명령 확인

## 테스트

실제 카드 리더기 없이 목 데이터를 사용하여 테스트할 수 있습니다.

### 테스트 실행

```bash
python test_card_reader.py
```

또는 unittest를 사용:

```bash
python -m unittest test_card_reader.py -v
```

### 테스트 내용

- 카드 리더기 연결 성공/실패 시나리오
- SELECT APDU 명령 테스트
- 카드번호 조회 명령 테스트
- 다양한 응답 길이에 따른 카드번호 추출 테스트
- 클립보드 복사 기능 테스트
- 메인 함수 통합 테스트
- T-money 카드 시나리오 테스트

모든 테스트는 `unittest.mock`을 사용하여 실제 하드웨어 없이 실행됩니다.

## 참고 자료

- ISO/IEC 14443 표준
- ISO/IEC 7816-4 APDU 명령 형식
- 금융IC카드 표준(개방형) - 한국은행
- [APDU 명령어 이해](https://hpkaushik121.medium.com/understanding-apdu-commands-emv-transaction-flow-part-2-d4e8df07eec)

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.


