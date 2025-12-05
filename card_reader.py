#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISO/IEC 14443 Type A/B 카드 리더기 프로그램
카드 번호를 읽어서 클립보드에 복사하는 기능 제공
"""

import logging
import time
from typing import Optional, Tuple
import pyperclip

# pyscard import (PC/SC 라이브러리 필요)
# abort trap을 방지하기 위해 import를 안전하게 처리
PCSC_AVAILABLE = False
try:
    import os
    # 환경 변수로 abort trap 방지 시도
    os.environ.setdefault('DYLD_FALLBACK_LIBRARY_PATH', '')
    
    from smartcard.System import readers
    from smartcard.util import toHexString
    from smartcard.Exceptions import CardConnectionException, NoCardException
    PCSC_AVAILABLE = True
except (ImportError, OSError, SystemError, Exception) as e:
    # 모든 예외 처리 (abort trap 포함)
    import sys
    if '--verbose' in sys.argv or '-v' in sys.argv:
        logging.warning(f"pyscard를 import할 수 없습니다: {e}")
        logging.warning("PC/SC 라이브러리가 설치되어 있는지 확인하세요: brew install pcsc-lite")
    # 더미 클래스 정의
    class CardConnectionException(Exception):
        pass
    class NoCardException(Exception):
        pass
    def readers():
        return []
    def toHexString(data):
        return ' '.join([f'{b:02X}' for b in data])

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CardReader:
    """카드 리더기 클래스"""
    
    # APDU 명령 배열 선언
    SELECT_APDU = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x42, 0x00]  # SELECT by AID
    CARD_NUMBER_APDU = [0x90, 0x4C, 0x00, 0x00, 0x04]  # 카드번호 조회
    
    def __init__(self):
        """카드 리더기 초기화"""
        self.connection = None
        self.reader = None
        
    def connect_to_reader(self) -> bool:
        """
        카드 리더기에 연결 시도
        
        Returns:
            bool: 연결 성공 여부
        """
        if not PCSC_AVAILABLE:
            logger.error("PC/SC 라이브러리를 사용할 수 없습니다. brew install pcsc-lite로 설치하세요.")
            return False
        
        try:
            # 사용 가능한 리더기 목록 가져오기
            available_readers = readers()
            
            if not available_readers:
                logger.error("사용 가능한 카드 리더기를 찾을 수 없습니다.")
                return False
            
            # 첫 번째 리더기 사용
            self.reader = available_readers[0]
            logger.info(f"리더기 연결 시도: {self.reader}")
            
            # 카드 연결 (카드가 없어도 연결은 성공)
            self.connection = self.reader.createConnection()
            
            try:
                self.connection.connect()
                logger.info("카드 리더기 연결 성공 (카드 감지됨)")
            except NoCardException:
                # 카드가 없어도 리더기 연결은 성공
                logger.info("카드 리더기 연결 성공 (카드 없음 - 나중에 카드를 올려주세요)")
            
            return True
        except CardConnectionException as e:
            logger.error(f"카드 연결 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"리더기 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """카드 리더기 연결 해제"""
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("카드 리더기 연결 해제")
            except Exception as e:
                logger.error(f"연결 해제 오류: {e}")
    
    def check_card_presence(self) -> bool:
        """
        카드가 리더기에 있는지 확인
        
        Returns:
            bool: 카드 존재 여부
        """
        try:
            if not self.connection:
                return False
            
            # 연결이 끊어진 경우 재연결 시도
            try:
                # 간단한 명령으로 카드 응답 확인
                response, sw1, sw2 = self.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                
                # 성공 응답 코드 확인 (90 00)
                if sw1 == 0x90 and sw2 == 0x00:
                    return True
                else:
                    return False
            except (NoCardException, CardConnectionException):
                # 카드가 없거나 연결이 끊어진 경우 재연결 시도
                try:
                    self.connection.connect()
                    # 재연결 후 다시 확인
                    response, sw1, sw2 = self.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                    if sw1 == 0x90 and sw2 == 0x00:
                        return True
                    return False
                except NoCardException:
                    return False
                
        except Exception as e:
            error_msg = str(e)
            # 카드 제거/리셋 오류는 경고로 처리 (정상적인 상황)
            if "Card was removed" in error_msg or "0x80100069" in error_msg:
                # 카드가 제거되었으므로 재연결 시도
                try:
                    if self.connection:
                        self.connection.connect()
                except:
                    pass
                return False
            elif "Card was reset" in error_msg or "0x80100068" in error_msg:
                # 카드가 리셋되었으므로 재연결 시도
                try:
                    if self.connection:
                        self.connection.connect()
                except:
                    pass
                return False
            else:
                # 다른 오류인 경우 재연결 시도
                try:
                    if self.connection:
                        self.connection.connect()
                except:
                    pass
                return False
    
    def select_card(self) -> Tuple[bool, Optional[bytes]]:
        """
        SELECT APDU를 사용하여 카드 선택
        
        Returns:
            Tuple[bool, Optional[bytes]]: (성공 여부, 응답 데이터)
        """
        try:
            logger.info(f"SELECT APDU 전송: {toHexString(self.SELECT_APDU)}")
            
            response, sw1, sw2 = self.connection.transmit(self.SELECT_APDU)
            
            # 성공 응답 코드 확인
            if sw1 == 0x90 and sw2 == 0x00:
                logger.info("카드 선택 성공")
                response_bytes = bytes(response)
                logger.info(f"응답 데이터: {toHexString(response)}")
                return True, response_bytes
            else:
                logger.warning(f"카드 선택 실패. 응답 코드: {sw1:02X} {sw2:02X}")
                return False, None
                
        except Exception as e:
            error_msg = str(e)
            # 카드 제거/리셋 오류는 특별 처리
            if "Card was removed" in error_msg or "0x80100069" in error_msg:
                logger.warning("카드가 리더기에서 제거되었습니다. 카드를 다시 올려주세요.")
                return False, None
            elif "Card was reset" in error_msg or "0x80100068" in error_msg:
                logger.warning("카드가 리셋되었습니다. 카드를 다시 올려주세요.")
                return False, None
            logger.error(f"카드 선택 오류: {e}")
            return False, None
    
    def request_card_number(self) -> Tuple[bool, Optional[bytes]]:
        """
        카드 번호 요청 메서드
        
        Returns:
            Tuple[bool, Optional[bytes]]: (성공 여부, 응답 데이터)
        """
        try:
            logger.info(f"카드번호 조회 APDU 전송: {toHexString(self.CARD_NUMBER_APDU)}")
            
            response, sw1, sw2 = self.connection.transmit(self.CARD_NUMBER_APDU)
            
            # 성공 응답 코드 확인
            if sw1 == 0x90 and sw2 == 0x00:
                logger.info("카드번호 조회 성공")
                response_bytes = bytes(response)
                logger.info(f"응답 데이터: {toHexString(response)}")
                return True, response_bytes
            else:
                logger.warning(f"카드번호 조회 실패. 응답 코드: {sw1:02X} {sw2:02X}")
                return False, None
                
        except Exception as e:
            error_msg = str(e)
            # 카드 제거/리셋 오류는 특별 처리
            if "Card was removed" in error_msg or "0x80100069" in error_msg:
                logger.warning("카드가 리더기에서 제거되었습니다. 카드를 다시 올려주세요.")
                return False, None
            elif "Card was reset" in error_msg or "0x80100068" in error_msg:
                logger.warning("카드가 리셋되었습니다. 카드를 다시 올려주세요.")
                return False, None
            logger.error(f"카드번호 조회 오류: {e}")
            return False, None
    
    def extract_card_number(self, response_data: bytes) -> Optional[str]:
        """
        카드 번호 추출 메서드
        응답 데이터에서 카드 번호를 파싱하여 반환
        
        Args:
            response_data: 카드 응답 데이터
            
        Returns:
            Optional[str]: 추출된 카드 번호 (문자열)
        """
        try:
            if not response_data or len(response_data) < 4:
                logger.warning("응답 데이터가 너무 짧습니다.")
                return None
            
            # 응답 데이터를 16진수 문자열로 변환
            hex_string = ''.join([f'{b:02X}' for b in response_data])
            logger.info(f"파싱할 데이터: {hex_string}")
            
            # 카드번호 추출 로직
            # 예시 코드에 따르면 responseLength >= 24일 때 cardInfo + 8부터 8바이트가 카드번호
            # 하지만 실제 응답 구조는 카드 타입에 따라 다를 수 있음
            
            if len(response_data) >= 24:
                # 8번째 바이트부터 8바이트 추출
                card_number_bytes = response_data[8:16]
                card_number = ''.join([f'{b:02X}' for b in card_number_bytes])
                logger.info(f"추출된 카드번호: {card_number}")
                return card_number
            elif len(response_data) >= 4:
                # 응답이 짧은 경우 처음 4바이트를 카드번호로 사용
                card_number_bytes = response_data[:4]
                card_number = ''.join([f'{b:02X}' for b in card_number_bytes])
                logger.info(f"추출된 카드번호 (짧은 형식): {card_number}")
                return card_number
            else:
                # 전체 응답을 카드번호로 사용
                card_number = ''.join([f'{b:02X}' for b in response_data])
                logger.info(f"추출된 카드번호 (전체): {card_number}")
                return card_number
                
        except Exception as e:
            logger.error(f"카드번호 추출 오류: {e}")
            return None
    
    def copy_to_clipboard(self, text: str) -> bool:
        """
        클립보드 복사 함수
        
        Args:
            text: 복사할 텍스트
            
        Returns:
            bool: 복사 성공 여부
        """
        try:
            pyperclip.copy(text)
            logger.info(f"클립보드에 복사됨: {text}")
            return True
        except Exception as e:
            logger.error(f"클립보드 복사 오류: {e}")
            return False


def main():
    """메인 함수"""
    logger.info("카드 리더기 프로그램 시작")
    
    card_reader = CardReader()
    
    try:
        # 5.1 카드 리드 시도 (SDK 활용)
        logger.info("카드 리더기 연결 시도 중...")
        if not card_reader.connect_to_reader():
            logger.error("카드 리더기 연결 실패")
            return 1
        
        # 카드가 리더기에 있는지 확인
        time.sleep(0.5)  # 카드 안정화 대기
        if not card_reader.check_card_presence():
            logger.error("카드가 감지되지 않았습니다.")
            return 1
        
        # SELECT APDU로 카드 선택
        success, select_response = card_reader.select_card()
        if not success:
            logger.error("카드 선택 실패")
            return 1
        
        # 5.2 SELECT 응답에서 카드번호 추출 시도
        card_number = card_reader.extract_card_number(select_response)
        
        # SELECT 응답에서 카드번호를 찾지 못한 경우, 별도 명령으로 시도
        if not card_number:
            logger.info("SELECT 응답에서 카드번호를 찾지 못했습니다. 별도 명령으로 시도합니다.")
            success, card_number_response = card_reader.request_card_number()
            if success:
                # 5.3 카드 번호 추출
                card_number = card_reader.extract_card_number(card_number_response)
        if not card_number:
            logger.error("카드번호 추출 실패")
            return 1
        
        logger.info(f"최종 카드번호: {card_number}")
        
        # 5.4 클립보드에 복사
        if card_reader.copy_to_clipboard(card_number):
            logger.info("카드번호가 클립보드에 복사되었습니다.")
            print(f"\n카드번호: {card_number}")
            print("클립보드에 복사되었습니다.")
        else:
            logger.error("클립보드 복사 실패")
            return 1
        
        # 5.5 성공
        return 0
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return 1
    finally:
        card_reader.disconnect()


if __name__ == "__main__":
    exit(main())

