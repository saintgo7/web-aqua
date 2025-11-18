"""
센서 데이터 읽기 모듈
아두이노와 시리얼 통신으로 센서 데이터 수집
"""

import serial
import time
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorReader:
    """아두이노 센서 데이터 읽기 클래스"""

    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=2):
        """
        초기화
        :param port: 시리얼 포트 (라즈베리파이에서는 /dev/ttyUSB0 또는 /dev/ttyACM0)
        :param baudrate: 통신 속도
        :param timeout: 타임아웃 (초)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.last_data = {}

    def connect(self) -> bool:
        """시리얼 연결"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # 아두이노 리셋 대기
            logger.info(f"Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False

    def disconnect(self):
        """시리얼 연결 종료"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from Arduino")

    def read_data(self) -> Optional[Dict[str, float]]:
        """
        센서 데이터 읽기
        :return: 센서 데이터 딕셔너리 또는 None
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Serial connection not established")
            return None

        try:
            # 시리얼 데이터 읽기
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()

                # 에러 메시지 처리
                if line.startswith('ERROR'):
                    logger.error(f"Arduino error: {line}")
                    return None

                # 헤더 라인 무시
                if 'pH' in line or 'Format' in line or 'Started' in line:
                    return None

                # CSV 데이터 파싱: pH,Temperature,Humidity,Light,SoilMoisture
                parts = line.split(',')
                if len(parts) == 5:
                    data = {
                        'ph': float(parts[0]),
                        'temperature': float(parts[1]),
                        'humidity': float(parts[2]),
                        'light': int(parts[3]),
                        'soil_moisture': int(parts[4]),
                        'timestamp': time.time()
                    }
                    self.last_data = data
                    return data
                else:
                    logger.warning(f"Invalid data format: {line}")
                    return None
        except Exception as e:
            logger.error(f"Error reading sensor data: {e}")
            return None

        return None

    def send_command(self, command: str) -> bool:
        """
        아두이노에 명령 전송
        :param command: 명령 문자열
        :return: 성공 여부
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Serial connection not established")
            return False

        try:
            self.serial_conn.write(f"{command}\n".encode('utf-8'))
            time.sleep(0.1)

            # 응답 읽기
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode('utf-8').strip()
                logger.info(f"Arduino response: {response}")
                return response.startswith('OK')
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

        return False

    def get_last_data(self) -> Dict[str, float]:
        """마지막 센서 데이터 반환"""
        return self.last_data


if __name__ == '__main__':
    # 테스트 코드
    reader = SensorReader(port='/dev/ttyUSB0')

    if reader.connect():
        print("Reading sensor data... (Press Ctrl+C to stop)")
        try:
            while True:
                data = reader.read_data()
                if data:
                    print(f"pH: {data['ph']:.2f}, "
                          f"Temp: {data['temperature']:.1f}°C, "
                          f"Humidity: {data['humidity']:.1f}%, "
                          f"Light: {data['light']} lux, "
                          f"Soil: {data['soil_moisture']}%")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            reader.disconnect()
    else:
        print("Failed to connect to Arduino")
