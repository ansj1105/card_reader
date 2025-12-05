#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카드 리더기 프로그램 테스트 코드
목 데이터를 사용하여 실제 카드 리더기 없이 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO

# card_reader 모듈 import
from card_reader import CardReader


class TestCardReader(unittest.TestCase):
    """CardReader 클래스 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.card_reader = CardReader()
        
    def tearDown(self):
        """테스트 후 정리"""
        if self.card_reader.connection:
            self.card_reader.connection = None
    
    @patch('card_reader.readers')
    def test_connect_to_reader_success(self, mock_readers):
        """카드 리더기 연결 성공 테스트"""
        # 목 리더기 설정
        mock_reader = Mock()
        mock_connection = Mock()
        mock_reader.createConnection.return_value = mock_connection
        mock_readers.return_value = [mock_reader]
        
        # 연결 테스트
        result = self.card_reader.connect_to_reader()
        
        # 검증
        self.assertTrue(result)
        self.assertEqual(self.card_reader.reader, mock_reader)
        self.assertEqual(self.card_reader.connection, mock_connection)
        mock_connection.connect.assert_called_once()
    
    @patch('card_reader.readers')
    def test_connect_to_reader_no_readers(self, mock_readers):
        """리더기가 없을 때 테스트"""
        mock_readers.return_value = []
        
        result = self.card_reader.connect_to_reader()
        
        self.assertFalse(result)
    
    @patch('card_reader.readers')
    def test_connect_to_reader_no_card(self, mock_readers):
        """카드가 없을 때 테스트"""
        from smartcard.Exceptions import NoCardException
        
        mock_reader = Mock()
        mock_connection = Mock()
        mock_connection.connect.side_effect = NoCardException()
        mock_reader.createConnection.return_value = mock_connection
        mock_readers.return_value = [mock_reader]
        
        result = self.card_reader.connect_to_reader()
        
        self.assertFalse(result)
    
    def test_select_card_success(self):
        """SELECT APDU 성공 테스트"""
        # 목 연결 설정
        mock_connection = Mock()
        # 성공 응답: [0x01, 0x02, 0x03, ...] + SW1=0x90, SW2=0x00
        mock_connection.transmit.return_value = (
            [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 
             0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
             0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18], 
            0x90, 0x00
        )
        self.card_reader.connection = mock_connection
        
        # SELECT 실행
        success, response = self.card_reader.select_card()
        
        # 검증
        self.assertTrue(success)
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 24)
        mock_connection.transmit.assert_called_once_with(self.card_reader.SELECT_APDU)
    
    def test_select_card_failure(self):
        """SELECT APDU 실패 테스트"""
        mock_connection = Mock()
        # 실패 응답: SW1=0x6A, SW2=0x82 (파일 없음)
        mock_connection.transmit.return_value = ([], 0x6A, 0x82)
        self.card_reader.connection = mock_connection
        
        success, response = self.card_reader.select_card()
        
        self.assertFalse(success)
        self.assertIsNone(response)
    
    def test_request_card_number_success(self):
        """카드번호 조회 성공 테스트"""
        mock_connection = Mock()
        # 카드번호 조회 응답: 4바이트 카드번호
        mock_connection.transmit.return_value = (
            [0x12, 0x34, 0x56, 0x78], 
            0x90, 0x00
        )
        self.card_reader.connection = mock_connection
        
        success, response = self.card_reader.request_card_number()
        
        self.assertTrue(success)
        self.assertIsNotNone(response)
        self.assertEqual(len(response), 4)
        mock_connection.transmit.assert_called_once_with(self.card_reader.CARD_NUMBER_APDU)
    
    def test_extract_card_number_long_response(self):
        """긴 응답에서 카드번호 추출 테스트 (24바이트 이상)"""
        # 예시 코드 기준: 8번째 바이트부터 8바이트가 카드번호
        response_data = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,  # 0-7: 헤더
            0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,  # 8-15: 카드번호
            0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,  # 16-23: 기타 데이터
        ])
        
        card_number = self.card_reader.extract_card_number(response_data)
        
        self.assertIsNotNone(card_number)
        self.assertEqual(card_number, "123456789ABCDEF0")
    
    def test_extract_card_number_short_response(self):
        """짧은 응답에서 카드번호 추출 테스트 (4바이트 이상, 24바이트 미만)"""
        response_data = bytes([0x12, 0x34, 0x56, 0x78])
        
        card_number = self.card_reader.extract_card_number(response_data)
        
        self.assertIsNotNone(card_number)
        self.assertEqual(card_number, "12345678")
    
    def test_extract_card_number_very_short_response(self):
        """매우 짧은 응답에서 카드번호 추출 테스트"""
        response_data = bytes([0x12, 0x34, 0x56, 0x78, 0x9A])
        
        card_number = self.card_reader.extract_card_number(response_data)
        
        self.assertIsNotNone(card_number)
        # 전체 응답을 카드번호로 사용
        self.assertEqual(card_number, "123456789A")
    
    def test_extract_card_number_invalid_response(self):
        """잘못된 응답 테스트"""
        # None 테스트
        card_number = self.card_reader.extract_card_number(None)
        self.assertIsNone(card_number)
        
        # 빈 바이트 테스트
        card_number = self.card_reader.extract_card_number(bytes([]))
        self.assertIsNone(card_number)
        
        # 너무 짧은 응답 테스트
        card_number = self.card_reader.extract_card_number(bytes([0x12, 0x34]))
        self.assertIsNone(card_number)
    
    @patch('card_reader.pyperclip')
    def test_copy_to_clipboard_success(self, mock_pyperclip):
        """클립보드 복사 성공 테스트"""
        test_text = "123456789ABCDEF0"
        
        result = self.card_reader.copy_to_clipboard(test_text)
        
        self.assertTrue(result)
        mock_pyperclip.copy.assert_called_once_with(test_text)
    
    @patch('card_reader.pyperclip')
    def test_copy_to_clipboard_failure(self, mock_pyperclip):
        """클립보드 복사 실패 테스트"""
        mock_pyperclip.copy.side_effect = Exception("클립보드 오류")
        
        result = self.card_reader.copy_to_clipboard("test")
        
        self.assertFalse(result)
    
    def test_check_card_presence_success(self):
        """카드 존재 확인 성공 테스트"""
        mock_connection = Mock()
        mock_connection.transmit.return_value = ([0x12, 0x34, 0x56, 0x78], 0x90, 0x00)
        self.card_reader.connection = mock_connection
        
        result = self.card_reader.check_card_presence()
        
        self.assertTrue(result)
    
    def test_check_card_presence_no_connection(self):
        """연결이 없을 때 카드 존재 확인 테스트"""
        self.card_reader.connection = None
        
        result = self.card_reader.check_card_presence()
        
        self.assertFalse(result)
    
    def test_disconnect(self):
        """연결 해제 테스트"""
        mock_connection = Mock()
        self.card_reader.connection = mock_connection
        
        self.card_reader.disconnect()
        
        mock_connection.disconnect.assert_called_once()


class TestMainFunction(unittest.TestCase):
    """메인 함수 통합 테스트"""
    
    @patch('card_reader.CardReader')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_success(self, mock_stdout, mock_card_reader_class):
        """메인 함수 성공 시나리오 테스트"""
        # CardReader 인스턴스 모킹
        mock_reader = Mock()
        mock_card_reader_class.return_value = mock_reader
        
        # 각 메서드 모킹
        mock_reader.connect_to_reader.return_value = True
        mock_reader.check_card_presence.return_value = True
        mock_reader.select_card.return_value = (
            True, 
            bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
                   0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,
                   0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17])
        )
        mock_reader.extract_card_number.return_value = "123456789ABCDEF0"
        mock_reader.copy_to_clipboard.return_value = True
        
        # 메인 함수 import 및 실행
        from card_reader import main
        
        result = main()
        
        # 검증
        self.assertEqual(result, 0)
        mock_reader.connect_to_reader.assert_called_once()
        mock_reader.check_card_presence.assert_called_once()
        mock_reader.select_card.assert_called_once()
        mock_reader.extract_card_number.assert_called()
        mock_reader.copy_to_clipboard.assert_called_once_with("123456789ABCDEF0")
        mock_reader.disconnect.assert_called_once()
    
    @patch('card_reader.CardReader')
    def test_main_connection_failure(self, mock_card_reader_class):
        """메인 함수 - 연결 실패 시나리오"""
        mock_reader = Mock()
        mock_card_reader_class.return_value = mock_reader
        mock_reader.connect_to_reader.return_value = False
        
        from card_reader import main
        
        result = main()
        
        self.assertEqual(result, 1)
        mock_reader.disconnect.assert_called_once()
    
    @patch('card_reader.CardReader')
    def test_main_card_not_detected(self, mock_card_reader_class):
        """메인 함수 - 카드 미감지 시나리오"""
        mock_reader = Mock()
        mock_card_reader_class.return_value = mock_reader
        mock_reader.connect_to_reader.return_value = True
        mock_reader.check_card_presence.return_value = False
        
        from card_reader import main
        
        result = main()
        
        self.assertEqual(result, 1)
        mock_reader.disconnect.assert_called_once()
    
    @patch('card_reader.CardReader')
    def test_main_select_failure(self, mock_card_reader_class):
        """메인 함수 - SELECT 실패 시나리오"""
        mock_reader = Mock()
        mock_card_reader_class.return_value = mock_reader
        mock_reader.connect_to_reader.return_value = True
        mock_reader.check_card_presence.return_value = True
        mock_reader.select_card.return_value = (False, None)
        
        from card_reader import main
        
        result = main()
        
        self.assertEqual(result, 1)
        mock_reader.disconnect.assert_called_once()


class TestCardNumberExtractionScenarios(unittest.TestCase):
    """카드번호 추출 시나리오별 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.card_reader = CardReader()
    
    def test_tmoney_card_scenario(self):
        """T-money 카드 시나리오 테스트 (예시 코드 기반)"""
        # 예시 코드에서 cardInfo + 8부터 8바이트가 카드번호
        # responseLength >= 24
        tmoney_response = bytes([
            0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,  # 헤더 (0-7)
            0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0,  # 카드번호 (8-15)
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,  # 날짜 등 (16-23)
        ])
        
        card_number = self.card_reader.extract_card_number(tmoney_response)
        
        self.assertEqual(card_number, "123456789ABCDEF0")
    
    def test_short_card_number_scenario(self):
        """짧은 카드번호 시나리오"""
        short_response = bytes([0xAA, 0xBB, 0xCC, 0xDD])
        
        card_number = self.card_reader.extract_card_number(short_response)
        
        self.assertEqual(card_number, "AABBCCDD")
    
    def test_balance_query_response(self):
        """잔액 조회 응답 형식 테스트 (참고용)"""
        # 잔액 조회는 4바이트 응답
        balance_response = bytes([0x00, 0x01, 0x86, 0xA0])  # 100000원
        
        card_number = self.card_reader.extract_card_number(balance_response)
        
        # 짧은 응답이므로 전체를 카드번호로 사용
        self.assertEqual(card_number, "000186A0")


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 모든 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestCardReader))
    suite.addTests(loader.loadTestsFromTestCase(TestMainFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestCardNumberExtractionScenarios))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

