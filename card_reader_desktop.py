#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISO/IEC 14443 Type A/B 카드 리더기 데스크톱 애플리케이션
전체 화면에서 입력 필드에 자동으로 카드번호를 입력하는 기능 제공
PyQt5 기반
"""

import sys
import threading
import time
import logging
import traceback
from datetime import datetime
from typing import Optional
import pyautogui
import pyperclip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, QCheckBox,
                             QListWidget, QMessageBox, QGroupBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
from card_reader import CardReader, PCSC_AVAILABLE, logger

# pyautogui 안전 설정 (마우스가 모서리에 가면 중단)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # 각 동작 사이 0.1초 대기

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 전역 예외 핸들러
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """전역 예외 핸들러 - 치명적 오류 처리"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"치명적 오류 발생:\n{error_msg}")
    
    # 사용자에게 알림 (QApplication이 있을 때만)
    try:
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("치명적 오류")
            msg.setText("치명적 오류가 발생했습니다.")
            msg.setDetailedText(error_msg)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    except:
        pass

# 전역 예외 핸들러 등록
sys.excepthook = global_exception_handler


class AutoReadThread(QThread):
    """자동 읽기 스레드"""
    card_read = pyqtSignal(str)  # 카드번호 읽기 성공 시그널
    
    def __init__(self, card_reader, parent=None):
        super().__init__(parent)
        self.card_reader = card_reader
        self.stop_flag = False
        self.last_card_number = None
    
    def run(self):
        """자동 읽기 루프"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while not self.stop_flag:
            try:
                if self.card_reader:
                    try:
                        # 카드 존재 확인
                        if self.card_reader.check_card_presence():
                            # 카드 읽기
                            success, select_response = self.card_reader.select_card()
                            if success:
                                card_number = self.card_reader.extract_card_number(select_response)
                                
                                if not card_number:
                                    success, card_number_response = self.card_reader.request_card_number()
                                    if success:
                                        card_number = self.card_reader.extract_card_number(card_number_response)
                                
                                # 새로운 카드가 감지되었을 때만 처리
                                if card_number and card_number != self.last_card_number:
                                    # 카드번호 검증
                                    if len(card_number) == 16 and (card_number.isdigit() or all(c in '0123456789ABCDEFabcdef' for c in card_number)):
                                        self.card_read.emit(card_number)
                                        self.last_card_number = card_number
                                        consecutive_errors = 0  # 성공 시 오류 카운터 리셋
                            else:
                                consecutive_errors += 1
                        else:
                            self.last_card_number = None
                            consecutive_errors = 0  # 카드가 없으면 정상 상태
                    except Exception as e:
                        error_msg = str(e)
                        # 카드 제거/리셋은 정상적인 상황
                        if "Card was removed" in error_msg or "0x80100069" in error_msg:
                            consecutive_errors = 0
                        elif "Card was reset" in error_msg or "0x80100068" in error_msg:
                            consecutive_errors = 0
                        else:
                            consecutive_errors += 1
                            logger.warning(f"자동 읽기 오류: {e}")
                            
                            # 연속 오류가 너무 많으면 재연결 시도
                            if consecutive_errors >= max_consecutive_errors:
                                logger.error(f"연속 오류 {consecutive_errors}회 발생. 재연결 시도...")
                                try:
                                    if self.card_reader:
                                        self.card_reader.disconnect()
                                        time.sleep(0.5)
                                        self.card_reader.connect_to_reader()
                                        consecutive_errors = 0
                                except Exception as reconnect_error:
                                    logger.error(f"재연결 실패: {reconnect_error}")
                                    # 재연결 실패 시 더 긴 대기
                                    time.sleep(5)
                                    consecutive_errors = 0
                
                time.sleep(1)  # 1초마다 체크
            except Exception as e:
                error_msg = str(e)
                consecutive_errors += 1
                logger.error(f"자동 읽기 치명적 오류: {e}")
                
                # 치명적 오류 발생 시 더 긴 대기
                if consecutive_errors >= max_consecutive_errors:
                    time.sleep(5)
                    consecutive_errors = 0
                else:
                    time.sleep(1)
    
    def stop(self):
        """스레드 중지"""
        self.stop_flag = True


class CardReaderDesktop(QMainWindow):
    """카드 리더기 데스크톱 애플리케이션"""
    
    def __init__(self):
        super().__init__()
        
        # 상태 변수
        self.card_reader = None
        self.is_connected = False
        self.is_reading = False
        self.auto_read_thread = None
        self.last_card_number = None
        self.card_history = []
        
        # UI 생성
        self.init_ui()
        
        # 초기 상태 업데이트
        self.update_status()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("카드 리더기 프로그램")
        self.setGeometry(100, 100, 600, 700)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 제목
        title_label = QLabel("카드 리더기 프로그램")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 상태 섹션
        status_group = QGroupBox("상태")
        status_layout = QVBoxLayout()
        
        # 연결 상태
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("연결 상태:"))
        self.connection_status_label = QLabel("연결 안됨")
        self.connection_status_label.setStyleSheet("color: red;")
        connection_layout.addWidget(self.connection_status_label)
        connection_layout.addStretch()
        status_layout.addLayout(connection_layout)
        
        # PC/SC 상태
        pcsc_layout = QHBoxLayout()
        pcsc_layout.addWidget(QLabel("PC/SC 지원:"))
        if PCSC_AVAILABLE:
            self.pcsc_status_label = QLabel("지원됨")
            self.pcsc_status_label.setStyleSheet("color: green;")
        else:
            self.pcsc_status_label = QLabel("지원 안됨")
            self.pcsc_status_label.setStyleSheet("color: red;")
        pcsc_layout.addWidget(self.pcsc_status_label)
        pcsc_layout.addStretch()
        status_layout.addLayout(pcsc_layout)
        
        # PC/SC 미지원 안내
        if not PCSC_AVAILABLE:
            help_label = QLabel("PC/SC 라이브러리가 설치되지 않았습니다.\nmacOS: brew install pcsc-lite\nLinux: sudo apt-get install pcscd libpcsclite-dev")
            help_label.setStyleSheet("color: orange;")
            help_label.setWordWrap(True)
            status_layout.addWidget(help_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 버튼 섹션
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("리더기 연결")
        self.connect_button.clicked.connect(self.toggle_connection)
        button_layout.addWidget(self.connect_button)
        
        self.read_button = QPushButton("카드 읽기")
        self.read_button.clicked.connect(self.read_card)
        self.read_button.setEnabled(False)
        button_layout.addWidget(self.read_button)
        
        self.copy_button = QPushButton("클립보드 복사")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        main_layout.addLayout(button_layout)
        
        # 옵션 섹션
        option_group = QGroupBox("옵션")
        option_layout = QVBoxLayout()
        
        self.auto_read_checkbox = QCheckBox("자동 읽기 (카드 감지 시)")
        self.auto_read_checkbox.setChecked(True)
        self.auto_read_checkbox.stateChanged.connect(self.toggle_auto_read)
        option_layout.addWidget(self.auto_read_checkbox)
        
        self.auto_paste_checkbox = QCheckBox("자동 입력 (전체 화면)")
        self.auto_paste_checkbox.setChecked(True)
        self.auto_paste_checkbox.stateChanged.connect(self.toggle_auto_paste)
        option_layout.addWidget(self.auto_paste_checkbox)
        
        # 안내 메시지
        info_label = QLabel("💡 자동 입력 기능: 카드 번호를 읽으면 현재 포커스된 입력 필드에 자동으로 입력됩니다.")
        info_label.setStyleSheet("color: blue; font-size: 9pt;")
        info_label.setWordWrap(True)
        option_layout.addWidget(info_label)
        
        option_group.setLayout(option_layout)
        main_layout.addWidget(option_group)
        
        # 카드번호 표시 섹션
        card_group = QGroupBox("카드번호")
        card_layout = QVBoxLayout()
        
        self.card_number_label = QLabel("카드를 읽어주세요")
        card_font = QFont()
        card_font.setFamily("Courier")
        card_font.setPointSize(14)
        self.card_number_label.setFont(card_font)
        self.card_number_label.setStyleSheet("color: gray;")
        card_layout.addWidget(self.card_number_label)
        
        card_group.setLayout(card_layout)
        main_layout.addWidget(card_group)
        
        # 히스토리 섹션
        history_group = QGroupBox("읽은 카드 히스토리")
        history_layout = QVBoxLayout()
        
        # 히스토리 헤더
        history_header = QHBoxLayout()
        history_header.addWidget(QLabel("최근 읽은 카드 번호:"))
        history_header.addStretch()
        clear_button = QPushButton("전체 삭제")
        clear_button.clicked.connect(self.clear_history)
        history_header.addWidget(clear_button)
        history_layout.addLayout(history_header)
        
        # 히스토리 리스트
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.on_history_select)
        history_layout.addWidget(self.history_list)
        
        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group)
        
        # 로그 섹션
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
    
    def add_log(self, message: str, level: str = "INFO"):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.append(log_entry)
        
        # 로그 레벨에 따른 색상
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info(message)
        else:
            logger.info(message)
    
    def update_status(self):
        """상태 업데이트"""
        if self.is_connected:
            self.connection_status_label.setText("연결됨")
            self.connection_status_label.setStyleSheet("color: green;")
            self.connect_button.setText("연결 해제")
            self.read_button.setEnabled(True)
        else:
            self.connection_status_label.setText("연결 안됨")
            self.connection_status_label.setStyleSheet("color: red;")
            self.connect_button.setText("리더기 연결")
            self.read_button.setEnabled(False)
    
    def toggle_connection(self):
        """리더기 연결/해제"""
        try:
            if not PCSC_AVAILABLE:
                QMessageBox.critical(self, "오류", "PC/SC 라이브러리를 사용할 수 없습니다.\n설치 방법:\nmacOS: brew install pcsc-lite\nLinux: sudo apt-get install pcscd libpcsclite-dev")
                return
            
            if self.is_connected:
                # 연결 해제
                try:
                    if self.auto_read_thread:
                        self.auto_read_thread.stop()
                        self.auto_read_thread.wait(3000)  # 최대 3초 대기
                        self.auto_read_thread = None
                except Exception as e:
                    logger.warning(f"자동 읽기 스레드 종료 오류: {e}")
                
                try:
                    if self.card_reader:
                        self.card_reader.disconnect()
                        self.card_reader = None
                except Exception as e:
                    logger.warning(f"리더기 연결 해제 오류: {e}")
                
                self.is_connected = False
                self.add_log("리더기 연결 해제됨", "INFO")
            else:
                # 연결 시도 (재시도 로직 포함)
                self.connect_button.setEnabled(False)
                self.add_log("리더기 연결 시도 중...", "INFO")
                
                def connect_thread():
                    max_retries = 3
                    retry_delay = 1  # 초
                    
                    for attempt in range(max_retries):
                        try:
                            self.card_reader = CardReader()
                            success = self.card_reader.connect_to_reader()
                            
                            if success:
                                self.is_connected = True
                                self.add_log("리더기 연결 성공", "SUCCESS")
                                # 자동 읽기 시작
                                if self.auto_read_checkbox.isChecked():
                                    self.start_auto_read()
                                break
                            else:
                                if attempt < max_retries - 1:
                                    self.add_log(f"리더기 연결 실패 (재시도 {attempt + 1}/{max_retries})...", "WARNING")
                                    time.sleep(retry_delay)
                                else:
                                    self.add_log("리더기 연결 실패 - 리더기를 확인하세요", "ERROR")
                                    QMessageBox.warning(
                                        self, 
                                        "연결 실패", 
                                        "리더기 연결에 실패했습니다.\n\n확인 사항:\n"
                                        "- 리더기가 연결되어 있는지 확인\n"
                                        "- 다른 프로그램에서 리더기를 사용 중이 아닌지 확인\n"
                                        "- PC/SC 라이브러리가 설치되어 있는지 확인"
                                    )
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"리더기 연결 오류 (시도 {attempt + 1}): {e}")
                            
                            if attempt < max_retries - 1:
                                self.add_log(f"연결 오류 발생 (재시도 {attempt + 1}/{max_retries}): {error_msg}", "WARNING")
                                time.sleep(retry_delay)
                            else:
                                self.add_log(f"리더기 연결 오류: {error_msg}", "ERROR")
                                QMessageBox.critical(
                                    self, 
                                    "연결 오류", 
                                    f"리더기 연결 중 오류가 발생했습니다:\n\n{error_msg}\n\n"
                                    "리더기와 PC/SC 라이브러리를 확인하세요."
                                )
                    
                    self.connect_button.setEnabled(True)
                    self.update_status()
                
                thread = threading.Thread(target=connect_thread, daemon=True)
                thread.start()
                return  # 비동기 연결이므로 여기서 반환
            
            self.update_status()
        except Exception as e:
            logger.error(f"연결 토글 오류: {e}")
            self.add_log(f"연결 토글 오류: {e}", "ERROR")
            QMessageBox.critical(self, "오류", f"연결 처리 중 오류가 발생했습니다:\n\n{e}")
            self.connect_button.setEnabled(True)
            self.update_status()
    
    def read_card(self):
        """카드 읽기"""
        if not self.is_connected or not self.card_reader:
            QMessageBox.critical(self, "오류", "먼저 리더기를 연결하세요.")
            return
        
        if self.is_reading:
            return
        
        self.is_reading = True
        self.read_button.setEnabled(False)
        
        def read_thread():
            try:
                self.add_log("카드 읽기 시작...", "INFO")
                
                # 카드 존재 확인
                if not self.card_reader.check_card_presence():
                    self.add_log("카드가 감지되지 않았습니다.", "WARNING")
                    self.read_button.setEnabled(True)
                    self.is_reading = False
                    return
                
                # SELECT APDU로 카드 선택
                success, select_response = self.card_reader.select_card()
                if not success:
                    self.add_log("카드 선택 실패", "ERROR")
                    self.read_button.setEnabled(True)
                    self.is_reading = False
                    return
                
                # SELECT 응답에서 카드번호 추출 시도
                card_number = self.card_reader.extract_card_number(select_response)
                
                # SELECT 응답에서 카드번호를 찾지 못한 경우, 별도 명령으로 시도
                if not card_number:
                    self.add_log("SELECT 응답에서 카드번호를 찾지 못했습니다. 별도 명령으로 시도합니다.", "INFO")
                    success, card_number_response = self.card_reader.request_card_number()
                    if success:
                        card_number = self.card_reader.extract_card_number(card_number_response)
                
                if card_number:
                    # 카드번호 검증 (16자리)
                    if len(card_number) == 16 and (card_number.isdigit() or all(c in '0123456789ABCDEFabcdef' for c in card_number)):
                        self.on_card_read_success(card_number)
                    else:
                        self.add_log(f"카드번호 검증 실패: {card_number} (길이: {len(card_number)})", "ERROR")
                        self.read_button.setEnabled(True)
                        self.is_reading = False
                else:
                    self.add_log("카드번호 추출 실패", "ERROR")
                    self.read_button.setEnabled(True)
                    self.is_reading = False
                    
            except Exception as e:
                error_msg = str(e)
                if "Card was removed" in error_msg or "0x80100069" in error_msg:
                    self.add_log("카드가 리더기에서 제거되었습니다. 카드를 다시 올려주세요.", "WARNING")
                elif "Card was reset" in error_msg or "0x80100068" in error_msg:
                    self.add_log("카드가 리셋되었습니다. 카드를 다시 올려주세요.", "WARNING")
                else:
                    self.add_log(f"카드 읽기 오류: {e}", "ERROR")
                self.read_button.setEnabled(True)
                self.is_reading = False
        
        thread = threading.Thread(target=read_thread, daemon=True)
        thread.start()
    
    def on_card_read_success(self, card_number: str):
        """카드 읽기 성공 처리"""
        self.card_number_label.setText(card_number)
        self.card_number_label.setStyleSheet("color: black;")
        self.copy_button.setEnabled(True)
        self.add_log(f"카드번호 읽기 성공: {card_number}", "SUCCESS")
        
        # 클립보드에 복사
        copied = self.card_reader.copy_to_clipboard(card_number)
        if copied:
            self.add_log("클립보드에 복사됨", "SUCCESS")
        
        # 자동 입력 시도
        if self.auto_paste_checkbox.isChecked():
            self.auto_paste_card_number(card_number)
        
        # 히스토리에 추가
        self.add_to_history(card_number)
        
        # UI 업데이트
        self.read_button.setEnabled(True)
        self.is_reading = False
        
        # 같은 카드번호가 아니면 메시지 표시
        if self.last_card_number != card_number:
            QMessageBox.information(self, "성공", f"카드번호를 읽었습니다: {card_number}\n{'자동 입력 완료' if self.auto_paste_checkbox.isChecked() else 'Ctrl+V로 붙여넣으세요'}")
            self.last_card_number = card_number
    
    def auto_paste_card_number(self, card_number: str):
        """전체 화면에서 카드번호 자동 입력"""
        try:
            # 짧은 대기 (사용자가 입력 필드에 포커스를 둘 시간)
            time.sleep(0.2)
            
            # Ctrl+V (또는 Cmd+V)로 붙여넣기 시뮬레이션
            # macOS는 Cmd, Windows/Linux는 Ctrl
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                pyautogui.hotkey('command', 'v')
            else:  # Windows, Linux
                pyautogui.hotkey('ctrl', 'v')
            
            self.add_log("자동 입력 완료 (Ctrl+V/Cmd+V 시뮬레이션)", "SUCCESS")
            return True
        except Exception as e:
            self.add_log(f"자동 입력 오류: {e}", "ERROR")
            return False
    
    def copy_to_clipboard(self):
        """클립보드 복사"""
        card_number = self.card_number_label.text()
        if not card_number or card_number == "카드를 읽어주세요":
            QMessageBox.critical(self, "오류", "복사할 카드번호가 없습니다.")
            return
        
        if self.card_reader:
            success = self.card_reader.copy_to_clipboard(card_number)
            if success:
                self.add_log(f"클립보드 복사: {card_number}", "SUCCESS")
                QMessageBox.information(self, "성공", "클립보드에 복사되었습니다.")
            else:
                self.add_log("클립보드 복사 실패", "ERROR")
                QMessageBox.critical(self, "오류", "클립보드 복사에 실패했습니다.")
    
    def toggle_auto_read(self):
        """자동 읽기 토글"""
        if self.auto_read_checkbox.isChecked() and self.is_connected:
            self.start_auto_read()
        else:
            if self.auto_read_thread:
                self.auto_read_thread.stop()
                self.auto_read_thread.wait()
                self.auto_read_thread = None
    
    def toggle_auto_paste(self):
        """자동 입력 토글"""
        pass  # 체크박스 상태는 이미 저장됨
    
    def start_auto_read(self):
        """자동 읽기 시작"""
        if self.auto_read_thread and self.auto_read_thread.isRunning():
            return
        
        if not self.card_reader:
            return
        
        self.auto_read_thread = AutoReadThread(self.card_reader)
        self.auto_read_thread.card_read.connect(self.on_card_read_success)
        self.auto_read_thread.start()
        self.add_log("자동 읽기 모드 활성화", "INFO")
    
    def add_to_history(self, card_number: str):
        """히스토리에 추가"""
        now = datetime.now()
        history_item = {
            "card_number": card_number,
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }
        
        # 중복 체크 (같은 카드번호가 최근에 추가되지 않았으면 추가)
        if not self.card_history or self.card_history[-1]["card_number"] != card_number:
            self.card_history.append(history_item)
            # 최대 100개까지만 저장
            if len(self.card_history) > 100:
                self.card_history.pop(0)
            
            # 리스트박스 업데이트
            self.update_history_listbox()
    
    def update_history_listbox(self):
        """히스토리 리스트박스 업데이트"""
        self.history_list.clear()
        for item in reversed(self.card_history):  # 최신순으로 표시
            display_text = f"{item['card_number']} - {item['date']} {item['time']}"
            self.history_list.addItem(display_text)
    
    def on_history_select(self, item):
        """히스토리 항목 선택 시 클립보드에 복사"""
        index = self.history_list.row(item)
        if 0 <= index < len(self.card_history):
            history_item = self.card_history[-(index+1)]  # 역순이므로
            card_number = history_item["card_number"]
            if self.card_reader:
                success = self.card_reader.copy_to_clipboard(card_number)
                if success:
                    self.add_log(f"히스토리에서 복사: {card_number}", "SUCCESS")
                    QMessageBox.information(self, "성공", f"클립보드에 복사되었습니다: {card_number}")
    
    def clear_history(self):
        """히스토리 전체 삭제"""
        reply = QMessageBox.question(self, "확인", "모든 히스토리를 삭제하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.card_history.clear()
            self.update_history_listbox()
            self.add_log("히스토리 전체 삭제", "INFO")
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.is_connected and self.card_reader:
            if self.auto_read_thread:
                self.auto_read_thread.stop()
                self.auto_read_thread.wait()
            self.card_reader.disconnect()
        event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    window = CardReaderDesktop()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
