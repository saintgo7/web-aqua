"""
자동 제어 모듈
센서 데이터 기반 자동 제어 로직
"""

import logging
import time
from typing import Dict, Callable

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available. Running in simulation mode.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoController:
    """스마트팜 자동 제어 클래스"""

    # GPIO 핀 설정 (BCM 모드)
    PIN_WATER_PUMP = 17    # 워터 펌프 릴레이
    PIN_LED_LIGHT = 27     # LED 조명 릴레이
    PIN_FAN = 22           # 환풍기 릴레이

    # 제어 기준값
    THRESHOLDS = {
        'ph_min': 5.5,
        'ph_max': 6.5,
        'temp_min': 18.0,
        'temp_max': 28.0,
        'humidity_min': 60.0,
        'humidity_max': 80.0,
        'light_min': 300,      # lux
        'soil_moisture_min': 40  # %
    }

    def __init__(self, auto_mode=True):
        """
        초기화
        :param auto_mode: 자동 제어 모드 활성화 여부
        """
        self.auto_mode = auto_mode
        self.device_status = {
            'water_pump': False,
            'led_light': False,
            'fan': False
        }
        self.alerts = []

        # GPIO 초기화
        if GPIO_AVAILABLE:
            self._setup_gpio()
        else:
            logger.warning("Running in simulation mode - GPIO not available")

    def _setup_gpio(self):
        """GPIO 핀 초기화"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # 릴레이 핀을 출력으로 설정 (초기값 LOW = OFF)
        GPIO.setup(self.PIN_WATER_PUMP, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_LED_LIGHT, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_FAN, GPIO.OUT, initial=GPIO.LOW)

        logger.info("GPIO initialized")

    def process_sensor_data(self, sensor_data: Dict[str, float]):
        """
        센서 데이터 처리 및 제어
        :param sensor_data: 센서 데이터 딕셔너리
        """
        if not self.auto_mode:
            return

        self.alerts.clear()

        # pH 체크 (경고만, 자동 제어 없음)
        ph = sensor_data.get('ph', 7.0)
        if ph < self.THRESHOLDS['ph_min']:
            self.alerts.append(f"Warning: pH too low ({ph:.2f})")
        elif ph > self.THRESHOLDS['ph_max']:
            self.alerts.append(f"Warning: pH too high ({ph:.2f})")

        # 온도 체크 - 높으면 환풍기 작동
        temp = sensor_data.get('temperature', 20.0)
        if temp > self.THRESHOLDS['temp_max']:
            self.control_fan(True)
            self.alerts.append(f"High temperature ({temp:.1f}°C) - Fan ON")
        elif temp < self.THRESHOLDS['temp_max'] - 2:  # 히스테리시스
            self.control_fan(False)

        # 습도 체크
        humidity = sensor_data.get('humidity', 70.0)
        if humidity < self.THRESHOLDS['humidity_min']:
            self.alerts.append(f"Low humidity ({humidity:.1f}%)")
        elif humidity > self.THRESHOLDS['humidity_max']:
            self.alerts.append(f"High humidity ({humidity:.1f}%)")

        # 조도 체크 - 어두우면 LED 점등
        light = sensor_data.get('light', 500)
        if light < self.THRESHOLDS['light_min']:
            self.control_led(True)
            logger.info(f"Low light ({light} lux) - LED ON")
        else:
            self.control_led(False)

        # 토양 수분 체크 - 낮으면 워터 펌프 작동
        soil_moisture = sensor_data.get('soil_moisture', 50)
        if soil_moisture < self.THRESHOLDS['soil_moisture_min']:
            self.control_water_pump(True)
            self.alerts.append(f"Low soil moisture ({soil_moisture}%) - Pump ON")
        else:
            self.control_water_pump(False)

    def control_water_pump(self, state: bool):
        """
        워터 펌프 제어
        :param state: True=ON, False=OFF
        """
        if self.device_status['water_pump'] == state:
            return

        self.device_status['water_pump'] = state
        if GPIO_AVAILABLE:
            GPIO.output(self.PIN_WATER_PUMP, GPIO.HIGH if state else GPIO.LOW)
        logger.info(f"Water pump: {'ON' if state else 'OFF'}")

    def control_led(self, state: bool):
        """
        LED 조명 제어
        :param state: True=ON, False=OFF
        """
        if self.device_status['led_light'] == state:
            return

        self.device_status['led_light'] = state
        if GPIO_AVAILABLE:
            GPIO.output(self.PIN_LED_LIGHT, GPIO.HIGH if state else GPIO.LOW)
        logger.info(f"LED light: {'ON' if state else 'OFF'}")

    def control_fan(self, state: bool):
        """
        환풍기 제어
        :param state: True=ON, False=OFF
        """
        if self.device_status['fan'] == state:
            return

        self.device_status['fan'] = state
        if GPIO_AVAILABLE:
            GPIO.output(self.PIN_FAN, GPIO.HIGH if state else GPIO.LOW)
        logger.info(f"Fan: {'ON' if state else 'OFF'}")

    def set_auto_mode(self, enabled: bool):
        """자동 모드 설정"""
        self.auto_mode = enabled
        logger.info(f"Auto mode: {'ENABLED' if enabled else 'DISABLED'}")

    def get_status(self) -> Dict:
        """현재 상태 반환"""
        return {
            'auto_mode': self.auto_mode,
            'devices': self.device_status.copy(),
            'alerts': self.alerts.copy(),
            'thresholds': self.THRESHOLDS.copy()
        }

    def manual_control(self, device: str, state: bool):
        """
        수동 제어
        :param device: 'water_pump', 'led_light', 'fan'
        :param state: True=ON, False=OFF
        """
        if device == 'water_pump':
            self.control_water_pump(state)
        elif device == 'led_light':
            self.control_led(state)
        elif device == 'fan':
            self.control_fan(state)
        else:
            logger.error(f"Unknown device: {device}")

    def cleanup(self):
        """GPIO 정리"""
        if GPIO_AVAILABLE:
            # 모든 장치 끄기
            self.control_water_pump(False)
            self.control_led(False)
            self.control_fan(False)
            GPIO.cleanup()
            logger.info("GPIO cleaned up")


if __name__ == '__main__':
    # 테스트 코드
    controller = AutoController(auto_mode=True)

    # 테스트 센서 데이터
    test_data = {
        'ph': 6.0,
        'temperature': 30.0,  # 높은 온도
        'humidity': 70.0,
        'light': 200,  # 어두움
        'soil_moisture': 30  # 낮은 수분
    }

    print("Processing test sensor data...")
    controller.process_sensor_data(test_data)

    status = controller.get_status()
    print(f"\nStatus: {status}")

    time.sleep(2)
    controller.cleanup()
