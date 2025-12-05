#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISO/IEC 14443 Type A/B 카드 리더기 프로그램 - 웹 버전
FastAPI + uvicorn을 사용한 웹 기반 인터페이스
"""

import logging
import threading
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from card_reader import CardReader, PCSC_AVAILABLE

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="카드 리더기 프로그램")

# 전역 카드 리더기 인스턴스
card_reader: Optional[CardReader] = None
is_connected = False
is_reading = False

# 카드 읽기 히스토리
card_history: List[Dict[str, str]] = []


# 요청/응답 모델
class StatusResponse(BaseModel):
    connected: bool
    reading: bool
    pcsc_available: bool
    message: str


class CardNumberResponse(BaseModel):
    success: bool
    card_number: Optional[str] = None
    message: str
    copied: bool = False


class HistoryItem(BaseModel):
    card_number: str
    timestamp: str
    date: str
    time: str


class HistoryResponse(BaseModel):
    history: List[HistoryItem]


# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카드 리더기 프로그램</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2em;
        }
        
        .status-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .status-label {
            font-weight: 600;
            color: #555;
        }
        
        .status-value {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .status-connected {
            background: #d4edda;
            color: #155724;
        }
        
        .status-disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-unavailable {
            background: #fff3cd;
            color: #856404;
        }
        
        .help-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .help-box h3 {
            color: #856404;
            margin-bottom: 10px;
        }
        
        .help-box p {
            color: #856404;
            line-height: 1.6;
        }
        
        .help-box code {
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #333;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        button {
            flex: 1;
            min-width: 150px;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .card-number-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .card-number-display {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 1.5em;
            text-align: center;
            color: #333;
            margin-bottom: 15px;
            word-break: break-all;
        }
        
        .log-section {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 5px;
        }
        
        .log-info {
            color: #17a2b8;
        }
        
        .log-success {
            color: #28a745;
        }
        
        .log-warning {
            color: #ffc107;
        }
        
        .log-error {
            color: #dc3545;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .message-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .message-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .history-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .history-header h3 {
            margin: 0;
            font-size: 1.1em;
            flex: 1;
        }
        
        .history-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .history-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .history-item:hover {
            background: #e9ecef;
            border-color: #667eea;
            transform: translateX(5px);
        }
        
        .history-item-info {
            flex: 1;
        }
        
        .history-item-number {
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .history-item-time {
            font-size: 0.85em;
            color: #6c757d;
        }
        
        .history-item-copy {
            padding: 8px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s;
            white-space: nowrap;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .history-item-copy:hover {
            background: #5568d3;
            transform: scale(1.05);
        }
        
        .history-item-copy:active {
            transform: scale(0.95);
        }
        
        .history-empty {
            text-align: center;
            color: #6c757d;
            padding: 40px;
            font-style: italic;
        }
        
        .btn-clear {
            background: #dc3545;
            color: white;
            padding: 6px 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            font-weight: 500;
            transition: all 0.2s;
            white-space: nowrap;
            height: 36px;
            flex-shrink: 0;
            width: auto;
        }
        
        .btn-clear:hover {
            background: #c82333;
            transform: scale(1.05);
        }
        
        .btn-clear:active {
            transform: scale(0.95);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>카드 리더기 프로그램</h1>
        
        <div id="message" class="message"></div>
        
        <div id="help-box" class="help-box" style="display: none;">
            <h3>⚠️ PC/SC 라이브러리 설치 필요</h3>
            <p id="help-message"></p>
            <div id="install-instructions" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ffc107;">
                <h4 style="margin-bottom: 10px; color: #856404;">설치 방법:</h4>
                <div id="install-steps"></div>
            </div>
        </div>
        
        <div class="status-section">
            <div class="status-item">
                <span class="status-label">연결 상태:</span>
                <span id="connection-status" class="status-value status-disconnected">연결 안됨</span>
            </div>
            <div class="status-item">
                <span class="status-label">PC/SC 지원:</span>
                <span id="pcsc-status" class="status-value">확인 중...</span>
            </div>
        </div>
        
        <div class="button-group">
            <button id="connect-btn" class="btn-primary" onclick="toggleConnection()">리더기 연결</button>
            <button id="read-btn" class="btn-success" onclick="readCard()" disabled>카드 읽기</button>
            <button id="copy-btn" class="btn-secondary" onclick="copyToClipboard()" disabled>클립보드 복사</button>
        </div>
        
        <div class="checkbox-group">
            <input type="checkbox" id="auto-read" onchange="toggleAutoRead()" checked>
            <label for="auto-read">자동 읽기 (카드 감지 시) - 기본 활성화</label>
        </div>
        
        <div class="card-number-section">
            <h3 style="margin-bottom: 15px;">카드번호</h3>
            <div id="card-number" class="card-number-display">카드를 읽어주세요</div>
        </div>
        
        <div class="history-section">
            <div class="history-header">
                <h3>읽은 카드 히스토리</h3>
                <button class="btn-clear" onclick="clearHistory()" title="모든 히스토리 삭제">전체 삭제</button>
            </div>
            <div class="history-list" id="history-list">
                <div class="history-empty">아직 읽은 카드가 없습니다.</div>
            </div>
        </div>
        
        <div class="log-section" id="log-section">
            <div class="log-entry log-info">프로그램 시작</div>
        </div>
    </div>
    
    <script>
        let autoReadInterval = null;
        let isAutoReadEnabled = false;
        
        // 상태 업데이트
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // 연결 상태
                const statusEl = document.getElementById('connection-status');
                const connectBtn = document.getElementById('connect-btn');
                const readBtn = document.getElementById('read-btn');
                
                if (data.connected) {
                    statusEl.textContent = '연결됨';
                    statusEl.className = 'status-value status-connected';
                    connectBtn.textContent = '연결 해제';
                    connectBtn.className = 'btn-danger';
                    readBtn.disabled = false;
                } else {
                    statusEl.textContent = '연결 안됨';
                    statusEl.className = 'status-value status-disconnected';
                    connectBtn.textContent = '리더기 연결';
                    connectBtn.className = 'btn-primary';
                    readBtn.disabled = true;
                }
                
                // PC/SC 상태
                const pcscStatus = document.getElementById('pcsc-status');
                const helpBox = document.getElementById('help-box');
                const helpMessage = document.getElementById('help-message');
                const installSteps = document.getElementById('install-steps');
                
                if (data.pcsc_available) {
                    pcscStatus.textContent = '지원됨';
                    pcscStatus.className = 'status-value status-connected';
                    helpBox.style.display = 'none';
                } else {
                    pcscStatus.textContent = '지원 안됨';
                    pcscStatus.className = 'status-value status-unavailable';
                    helpBox.style.display = 'block';
                    if (data.message) {
                        helpMessage.innerHTML = data.message.replace(/\\n/g, '<br>');
                    }
                    
                    // 운영체제별 설치 방법 표시
                    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
                    let installHtml = '';
                    
                    if (/Mac|iPhone|iPod|iPad/i.test(userAgent) || navigator.platform === 'MacIntel') {
                        // macOS
                        installHtml = `
                            <ol style="margin: 0; padding-left: 20px; color: #856404;">
                                <li style="margin-bottom: 8px;">터미널을 엽니다.</li>
                                <li style="margin-bottom: 8px;">다음 명령을 실행합니다:</li>
                                <li style="margin-bottom: 8px;">
                                    <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 5px;">
                                        brew install pcsc-lite
                                    </code>
                                </li>
                                <li style="margin-bottom: 8px;">설치 후 프로그램을 다시 시작합니다.</li>
                            </ol>
                        `;
                    } else if (/Linux/i.test(userAgent) || navigator.platform === 'Linux x86_64') {
                        // Linux
                        installHtml = `
                            <ol style="margin: 0; padding-left: 20px; color: #856404;">
                                <li style="margin-bottom: 8px;">터미널을 엽니다.</li>
                                <li style="margin-bottom: 8px;">다음 명령을 실행합니다:</li>
                                <li style="margin-bottom: 8px;">
                                    <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; display: block; margin-top: 5px;">
                                        sudo apt-get update<br>
                                        sudo apt-get install pcscd libpcsclite-dev<br>
                                        sudo systemctl start pcscd
                                    </code>
                                </li>
                                <li style="margin-bottom: 8px;">설치 후 프로그램을 다시 시작합니다.</li>
                            </ol>
                        `;
                    } else {
                        // Windows 또는 기타
                        installHtml = `
                            <p style="color: #856404; margin: 0;">
                                Windows는 PC/SC가 기본 제공됩니다. 문제가 있는 경우 Windows 업데이트를 확인하세요.
                            </p>
                        `;
                    }
                    
                    installSteps.innerHTML = installHtml;
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        // 연결 토글
        async function toggleConnection() {
            const connectBtn = document.getElementById('connect-btn');
            connectBtn.disabled = true;
            
            try {
                const response = await fetch('/api/connect', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    addLog(data.message, 'success');
                    if (data.connected) {
                        // 리더기 연결 성공 시 자동 읽기 시작
                        const checkbox = document.getElementById('auto-read');
                        checkbox.checked = true;
                        isAutoReadEnabled = true;
                        startAutoRead();
                        addLog('자동 읽기 모드 자동 활성화', 'info');
                    } else {
                        // 연결 해제 시 자동 읽기 중지
                        stopAutoRead();
                    }
                } else {
                    addLog(data.message, 'error');
                    showMessage(data.message, 'error');
                }
            } catch (error) {
                addLog('연결 오류: ' + error.message, 'error');
                showMessage('연결 오류가 발생했습니다.', 'error');
            } finally {
                connectBtn.disabled = false;
                updateStatus();
            }
        }
        
        // 카드번호 검증 (16자리 확인)
        function validateCardNumber(cardNumber) {
            if (!cardNumber || typeof cardNumber !== 'string') {
                return { valid: false, message: '카드번호가 유효하지 않습니다.' };
            }
            
            // 공백 제거
            const cleaned = cardNumber.trim();
            
            // 16진수 형식인지 확인 (예: "123456789ABCDEF0")
            const hexPattern = /^[0-9A-Fa-f]{16}$/;
            // 숫자만 있는 형식인지 확인 (예: "1234567890123456")
            const numericPattern = /^[0-9]{16}$/;
            
            if (cleaned.length === 16) {
                if (hexPattern.test(cleaned) || numericPattern.test(cleaned)) {
                    return { valid: true, message: '카드번호 검증 성공' };
                } else {
                    return { valid: false, message: `카드번호 형식이 올바르지 않습니다. (길이: ${cleaned.length}, 값: ${cleaned})` };
                }
            } else {
                return { valid: false, message: `카드번호가 16자리가 아닙니다. (현재 길이: ${cleaned.length}, 값: ${cleaned})` };
            }
        }
        
        // 현재 포커스된 입력 요소에 텍스트 삽입 (검증 포함)
        function pasteToFocusedInput(text) {
            // 먼저 카드번호 검증
            const validation = validateCardNumber(text);
            if (!validation.valid) {
                addLog('자동 삽입 실패: ' + validation.message, 'error');
                return false;
            }
            
            try {
                const activeElement = document.activeElement;
                
                // input 또는 textarea 요소인지 확인
                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                    const input = activeElement;
                    const start = input.selectionStart || 0;
                    const end = input.selectionEnd || 0;
                    const value = input.value || '';
                    
                    // 선택된 텍스트를 교체하거나 커서 위치에 삽입
                    const newValue = value.substring(0, start) + text + value.substring(end);
                    input.value = newValue;
                    
                    // 커서 위치 조정
                    const newCursorPos = start + text.length;
                    input.setSelectionRange(newCursorPos, newCursorPos);
                    
                    // input 이벤트 발생 (React 등 프레임워크에서 인식하도록)
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    addLog('입력창에 카드번호 삽입 성공: ' + text, 'success');
                    return true;
                }
            } catch (error) {
                addLog('입력 요소에 삽입 오류: ' + error.message, 'error');
                console.error('입력 요소에 삽입 오류:', error);
            }
            return false;
        }
        
        // 카드 읽기
        async function readCard() {
            const readBtn = document.getElementById('read-btn');
            readBtn.disabled = true;
            
            try {
                addLog('카드 읽기 시작...', 'info');
                const response = await fetch('/api/read', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success && data.card_number) {
                    document.getElementById('card-number').textContent = data.card_number;
                    document.getElementById('copy-btn').disabled = false;
                    
                    // 포커스된 입력창에 자동 삽입 시도
                    const pasted = pasteToFocusedInput(data.card_number);
                    
                    addLog('카드번호 읽기 성공: ' + data.card_number, 'success');
                    if (data.copied) {
                        if (pasted) {
                            showMessage('카드번호를 읽어 입력창에 삽입하고 클립보드에 복사했습니다.', 'success');
                        } else {
                            showMessage('카드번호를 읽었고 클립보드에 복사되었습니다.', 'success');
                        }
                    } else {
                        if (pasted) {
                            showMessage('카드번호를 읽어 입력창에 삽입했습니다.', 'success');
                        } else {
                            showMessage('카드번호를 읽었습니다.', 'success');
                        }
                    }
                    // 히스토리 업데이트
                    updateHistory();
                } else {
                    // 카드 제거/리셋 오류는 경고로 표시
                    if (data.message && (data.message.includes('제거') || data.message.includes('removed') || 
                        data.message.includes('리셋') || data.message.includes('reset'))) {
                        addLog(data.message, 'warning');
                        showMessage(data.message, 'info');
                    } else {
                        addLog(data.message, 'error');
                        showMessage(data.message, 'error');
                    }
                }
            } catch (error) {
                addLog('카드 읽기 오류: ' + error.message, 'error');
                showMessage('카드 읽기 오류가 발생했습니다.', 'error');
            } finally {
                readBtn.disabled = false;
            }
        }
        
        // 클립보드 복사 및 포커스된 입력창에 붙여넣기
        async function copyToClipboard() {
            const cardNumber = document.getElementById('card-number').textContent;
            if (!cardNumber || cardNumber === '카드를 읽어주세요') {
                showMessage('복사할 카드번호가 없습니다.', 'error');
                return;
            }
            
            try {
                // 먼저 포커스된 입력창에 직접 삽입 시도
                const pasted = pasteToFocusedInput(cardNumber);
                
                // 클립보드에도 복사
                const response = await fetch('/api/copy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ card_number: cardNumber })
                });
                const data = await response.json();
                
                if (data.success) {
                    if (pasted) {
                        showMessage('카드번호가 입력창에 삽입되고 클립보드에 복사되었습니다.', 'success');
                        addLog('입력창 삽입 및 클립보드 복사: ' + cardNumber, 'success');
                    } else {
                        showMessage('클립보드에 복사되었습니다. (Ctrl+V로 붙여넣기)', 'success');
                        addLog('클립보드 복사: ' + cardNumber, 'success');
                    }
                } else {
                    if (pasted) {
                        showMessage('카드번호가 입력창에 삽입되었습니다.', 'success');
                    } else {
                        showMessage(data.message, 'error');
                    }
                }
            } catch (error) {
                showMessage('복사 오류가 발생했습니다.', 'error');
            }
        }
        
        // 자동 읽기 토글
        function toggleAutoRead() {
            const checkbox = document.getElementById('auto-read');
            isAutoReadEnabled = checkbox.checked;
            
            if (isAutoReadEnabled) {
                startAutoRead();
                addLog('자동 읽기 모드 활성화', 'info');
            } else {
                stopAutoRead();
                addLog('자동 읽기 모드 비활성화', 'info');
            }
        }
        
        function startAutoRead() {
            if (autoReadInterval) return;
            let lastCardNumber = null; // 마지막으로 읽은 카드번호 저장
            let isReading = false; // 읽기 중 플래그
            
            autoReadInterval = setInterval(async () => {
                // 이미 읽는 중이면 스킵
                if (isReading) return;
                
                try {
                    // 카드 감지 API 먼저 호출
                    const detectResponse = await fetch('/api/detect');
                    const detectData = await detectResponse.json();
                    
                    if (!detectData.connected) {
                        // 리더기가 연결되지 않았으면 중지
                        stopAutoRead();
                        return;
                    }
                    
                    if (detectData.card_present) {
                        // 카드가 있으면 읽기 시도
                        isReading = true;
                        const response = await fetch('/api/read', {
                            method: 'POST'
                        });
                        const data = await response.json();
                        isReading = false;
                        
                        if (data.success && data.card_number) {
                            // 새로운 카드가 감지되었거나 다른 카드인 경우에만 처리
                            if (lastCardNumber !== data.card_number) {
                                document.getElementById('card-number').textContent = data.card_number;
                                document.getElementById('copy-btn').disabled = false;
                                
                                // 포커스된 입력창에 자동 삽입 시도
                                const pasted = pasteToFocusedInput(data.card_number);
                                
                                addLog('카드번호 자동 읽기 성공: ' + data.card_number, 'success');
                                if (data.copied) {
                                    if (pasted) {
                                        showMessage('카드번호를 읽어 입력창에 삽입하고 클립보드에 복사했습니다.', 'success');
                                    } else {
                                        showMessage('카드번호를 읽었고 클립보드에 복사되었습니다.', 'success');
                                    }
                                } else {
                                    if (pasted) {
                                        showMessage('카드번호를 읽어 입력창에 삽입했습니다.', 'success');
                                    } else {
                                        showMessage('카드번호를 읽었습니다.', 'success');
                                    }
                                }
                                lastCardNumber = data.card_number;
                                // 히스토리 업데이트
                                updateHistory();
                            }
                        } else if (data.message && (data.message.includes('감지되지 않았습니다') || 
                                   data.message.includes('제거') || data.message.includes('리셋'))) {
                            // 카드가 없거나 제거된 경우, 마지막 카드번호 초기화
                            if (lastCardNumber !== null) {
                                lastCardNumber = null;
                            }
                        }
                    } else {
                        // 카드가 없으면 마지막 카드번호 초기화
                        if (lastCardNumber !== null) {
                            lastCardNumber = null;
                        }
                    }
                } catch (error) {
                    isReading = false;
                    // 오류 발생 시 조용히 처리 (로그만 남김)
                    console.error('자동 읽기 오류:', error);
                }
            }, 1000); // 1초마다 체크
        }
        
        function stopAutoRead() {
            if (autoReadInterval) {
                clearInterval(autoReadInterval);
                autoReadInterval = null;
            }
        }
        
        // 로그 추가
        function addLog(message, level = 'info') {
            const logSection = document.getElementById('log-section');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${level}`;
            logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logSection.appendChild(logEntry);
            logSection.scrollTop = logSection.scrollHeight;
        }
        
        // 메시지 표시
        function showMessage(message, type) {
            const messageEl = document.getElementById('message');
            messageEl.textContent = message;
            messageEl.className = `message message-${type}`;
            messageEl.style.display = 'block';
            
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }
        
        // 히스토리 로드
        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                displayHistory(data.history);
            } catch (error) {
                console.error('히스토리 로드 오류:', error);
            }
        }
        
        // 히스토리 표시
        function displayHistory(history) {
            const historyList = document.getElementById('history-list');
            
            if (history.length === 0) {
                historyList.innerHTML = '<div class="history-empty">아직 읽은 카드가 없습니다.</div>';
                return;
            }
            
            historyList.innerHTML = '';
            history.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.onclick = () => copyHistoryCard(item.card_number);
                
                historyItem.innerHTML = `
                    <div class="history-item-info">
                        <div class="history-item-number">${item.card_number}</div>
                        <div class="history-item-time">${item.date} ${item.time}</div>
                    </div>
                    <button class="history-item-copy" onclick="event.stopPropagation(); copyHistoryCard('${item.card_number}')" title="클립보드에 복사">복사</button>
                `;
                
                historyList.appendChild(historyItem);
            });
        }
        
        // 히스토리 업데이트
        async function updateHistory() {
            await loadHistory();
        }
        
        // 히스토리에서 카드번호 복사
        async function copyHistoryCard(cardNumber) {
            try {
                const response = await fetch('/api/copy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ card_number: cardNumber })
                });
                const data = await response.json();
                
                if (data.success) {
                    showMessage('클립보드에 복사되었습니다: ' + cardNumber, 'success');
                    addLog('히스토리에서 복사: ' + cardNumber, 'success');
                } else {
                    showMessage(data.message, 'error');
                }
            } catch (error) {
                showMessage('복사 오류가 발생했습니다.', 'error');
            }
        }
        
        // 히스토리 전체 삭제
        async function clearHistory() {
            if (!confirm('모든 히스토리를 삭제하시겠습니까?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/history', {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (data.success) {
                    showMessage('히스토리가 삭제되었습니다.', 'success');
                    addLog('히스토리 전체 삭제', 'info');
                    await loadHistory();
                } else {
                    showMessage(data.message, 'error');
                }
            } catch (error) {
                showMessage('히스토리 삭제 오류가 발생했습니다.', 'error');
            }
        }
        
        // 초기화
        updateStatus();
        loadHistory();
        // status 업데이트 빈도 줄이기 (10초마다)
        setInterval(updateStatus, 10000);
        
        // 페이지 로드 시 자동 읽기 활성화 상태 확인
        const autoReadCheckbox = document.getElementById('auto-read');
        if (autoReadCheckbox.checked) {
            isAutoReadEnabled = true;
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    return HTML_TEMPLATE


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """상태 조회"""
    global is_connected, is_reading
    
    message = ""
    if not PCSC_AVAILABLE:
        import platform
        system = platform.system()
        if system == "Darwin":  # macOS
            message = "PC/SC 라이브러리를 사용할 수 없습니다. 다음 명령으로 설치하세요: brew install pcsc-lite (설치 후 가상환경 재생성: rm -rf venv && ./run_gui.sh)"
        elif system == "Linux":
            message = "PC/SC 라이브러리를 사용할 수 없습니다. 다음 명령으로 설치하세요: sudo apt-get install pcscd libpcsclite-dev"
        else:
            message = "PC/SC 라이브러리를 사용할 수 없습니다. PC/SC 드라이버를 설치하세요."
    
    return StatusResponse(
        connected=is_connected,
        reading=is_reading,
        pcsc_available=PCSC_AVAILABLE,
        message=message
    )


@app.get("/api/detect")
async def detect_card():
    """카드 감지 (로그 없이 빠른 확인)"""
    global card_reader, is_connected
    
    if not PCSC_AVAILABLE:
        return {"connected": False, "card_present": False}
    
    if not is_connected or not card_reader:
        return {"connected": False, "card_present": False}
    
    try:
        card_present = card_reader.check_card_presence()
        return {"connected": True, "card_present": card_present}
    except Exception:
        return {"connected": True, "card_present": False}


@app.post("/api/connect")
async def connect_reader():
    """리더기 연결/해제"""
    global card_reader, is_connected
    
    if not PCSC_AVAILABLE:
        raise HTTPException(status_code=503, detail="PC/SC 라이브러리를 사용할 수 없습니다.")
    
    try:
        if is_connected:
            # 연결 해제
            if card_reader:
                card_reader.disconnect()
                card_reader = None
            is_connected = False
            return {"success": True, "connected": False, "message": "리더기 연결 해제됨"}
        else:
            # 연결
            card_reader = CardReader()
            success = card_reader.connect_to_reader()
            
            if success:
                is_connected = True
                return {"success": True, "connected": True, "message": "리더기 연결 성공"}
            else:
                return {"success": False, "connected": False, "message": "리더기 연결 실패"}
    except Exception as e:
        logger.error(f"연결 오류: {e}")
        return {"success": False, "connected": False, "message": f"연결 오류: {str(e)}"}


@app.post("/api/read", response_model=CardNumberResponse)
async def read_card():
    """카드 읽기"""
    global card_reader, is_connected, is_reading
    
    if not PCSC_AVAILABLE:
        raise HTTPException(status_code=503, detail="PC/SC 라이브러리를 사용할 수 없습니다.")
    
    if not is_connected or not card_reader:
        raise HTTPException(status_code=400, detail="먼저 리더기를 연결하세요.")
    
    if is_reading:
        raise HTTPException(status_code=400, detail="이미 카드를 읽는 중입니다.")
    
    is_reading = True
    
    try:
        # 카드 존재 확인
        if not card_reader.check_card_presence():
            is_reading = False
            return CardNumberResponse(
                success=False,
                message="카드가 감지되지 않았습니다."
            )
        
        # SELECT APDU로 카드 선택
        success, select_response = card_reader.select_card()
        if not success:
            is_reading = False
            return CardNumberResponse(
                success=False,
                message="카드 선택 실패"
            )
        
        # SELECT 응답에서 카드번호 추출 시도
        card_number = card_reader.extract_card_number(select_response)
        
        # SELECT 응답에서 카드번호를 찾지 못한 경우, 별도 명령으로 시도
        if not card_number:
            logger.info("SELECT 응답에서 카드번호를 찾지 못했습니다. 별도 명령으로 시도합니다.")
            success, card_number_response = card_reader.request_card_number()
            if success:
                card_number = card_reader.extract_card_number(card_number_response)
        
        if card_number:
            # 클립보드에 자동 복사
            copied = card_reader.copy_to_clipboard(card_number)
            
            # 히스토리에 추가
            now = datetime.now()
            history_item = {
                "card_number": card_number,
                "timestamp": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            }
            # 중복 체크 (같은 카드번호가 최근에 추가되지 않았으면 추가)
            if not card_history or card_history[-1]["card_number"] != card_number:
                card_history.append(history_item)
                # 최대 100개까지만 저장
                if len(card_history) > 100:
                    card_history.pop(0)
            
            is_reading = False
            return CardNumberResponse(
                success=True,
                card_number=card_number,
                message="카드번호 읽기 성공",
                copied=copied
            )
        else:
            is_reading = False
            return CardNumberResponse(
                success=False,
                message="카드번호 추출 실패"
            )
            
    except Exception as e:
        error_msg = str(e)
        is_reading = False
        
        # 카드 제거/리셋 오류는 사용자 친화적인 메시지로 변환
        if "Card was removed" in error_msg or "0x80100069" in error_msg:
            return CardNumberResponse(
                success=False,
                message="카드가 리더기에서 제거되었습니다. 카드를 다시 올려주세요."
            )
        elif "Card was reset" in error_msg or "0x80100068" in error_msg:
            return CardNumberResponse(
                success=False,
                message="카드가 리셋되었습니다. 카드를 다시 올려주세요."
            )
        
        logger.error(f"카드 읽기 오류: {e}")
        return CardNumberResponse(
            success=False,
            message=f"카드 읽기 오류: {str(e)}"
        )


@app.post("/api/copy")
async def copy_card_number(request: Dict[str, str]):
    """클립보드 복사"""
    global card_reader
    
    card_number = request.get("card_number")
    if not card_number:
        raise HTTPException(status_code=400, detail="카드번호가 제공되지 않았습니다.")
    
    if not card_reader:
        card_reader = CardReader()
    
    success = card_reader.copy_to_clipboard(card_number)
    
    if success:
        return {"success": True, "message": "클립보드에 복사되었습니다."}
    else:
        return {"success": False, "message": "클립보드 복사 실패"}


@app.get("/api/history", response_model=HistoryResponse)
async def get_history():
    """히스토리 조회"""
    global card_history
    
    # 최신순으로 정렬 (최신이 마지막)
    history_items = [
        HistoryItem(
            card_number=item["card_number"],
            timestamp=item["timestamp"],
            date=item["date"],
            time=item["time"]
        )
        for item in card_history
    ]
    
    # 최신순으로 정렬 (역순)
    history_items.reverse()
    
    return HistoryResponse(history=history_items)


@app.delete("/api/history")
async def clear_history():
    """히스토리 전체 삭제"""
    global card_history
    
    card_history.clear()
    logger.info("히스토리 전체 삭제")
    
    return {"success": True, "message": "히스토리가 삭제되었습니다."}


def main():
    """메인 함수"""
    import uvicorn
    import logging as uvicorn_logging
    import webbrowser
    import threading
    import time
    import platform
    
    # uvicorn 액세스 로그 레벨 조정 (status 요청은 로그에 남기지 않음)
    uvicorn_logger = uvicorn_logging.getLogger("uvicorn.access")
    
    class StatusFilter(logging.Filter):
        def filter(self, record):
            # status API 요청은 로그에 남기지 않음
            if "/api/status" in record.getMessage():
                return False
            return True
    
    uvicorn_logger.addFilter(StatusFilter())
    
    logger.info("카드 리더기 웹 서버 시작")
    
    # PC/SC 라이브러리 설치 확인 및 안내
    if not PCSC_AVAILABLE:
        system = platform.system()
        print("\n" + "="*70)
        print("⚠️  PC/SC 라이브러리가 설치되지 않았습니다!")
        print("="*70)
        print("\n카드 읽기 기능을 사용하려면 PC/SC 라이브러리를 설치해야 합니다.\n")
        
        if system == "Darwin":  # macOS
            print("설치 방법:")
            print("  1. Homebrew가 설치되어 있어야 합니다.")
            print("  2. 다음 명령을 실행하세요:")
            print("     brew install pcsc-lite")
            print("  3. 설치 후 프로그램을 다시 시작하세요.")
        elif system == "Linux":
            print("설치 방법:")
            print("  Ubuntu/Debian:")
            print("    sudo apt-get update")
            print("    sudo apt-get install pcscd libpcsclite-dev")
            print("    sudo systemctl start pcscd")
            print("    sudo systemctl enable pcscd")
            print("\n  RedHat/CentOS:")
            print("    sudo yum install pcsc-lite pcsc-lite-devel")
            print("    sudo systemctl start pcscd")
            print("    sudo systemctl enable pcscd")
        else:  # Windows
            print("설치 방법:")
            print("  Windows는 PC/SC가 기본 제공됩니다.")
            print("  문제가 있는 경우 Windows 업데이트를 확인하세요.")
        
        print("\n" + "="*70)
        print("웹 인터페이스는 실행되지만 카드 읽기 기능은 작동하지 않습니다.")
        print("="*70 + "\n")
    
    # 브라우저 자동 실행 (약간의 지연 후)
    def open_browser():
        time.sleep(1.5)  # 서버 시작 대기
        webbrowser.open("http://localhost:8000")
        logger.info("브라우저가 자동으로 열렸습니다: http://localhost:8000")
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()

