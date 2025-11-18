"""
스마트팜 제어 시스템 메인 프로그램
센서 데이터 수집, 자동 제어, 웹 서버 통합
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from threading import Thread, Lock
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# 로컬 모듈 임포트
sys.path.insert(0, os.path.dirname(__file__))
from sensors.sensor_reader import SensorReader
from controllers.auto_controller import AutoController

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/smartfarm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__,
            template_folder='../web/templates',
            static_folder='../web/static')
CORS(app)

# 전역 변수
sensor_reader = None
auto_controller = None
current_data = {}
data_lock = Lock()
sensor_history = []
MAX_HISTORY = 100  # 최대 100개 데이터 포인트 저장


class SmartFarmSystem:
    """스마트팜 시스템 메인 클래스"""

    def __init__(self, serial_port='/dev/ttyUSB0'):
        """초기화"""
        global sensor_reader, auto_controller

        self.running = False

        # 센서 리더 초기화
        sensor_reader = SensorReader(port=serial_port)

        # 자동 제어기 초기화
        auto_controller = AutoController(auto_mode=True)

        logger.info("SmartFarm System initialized")

    def start(self):
        """시스템 시작"""
        # 센서 연결
        if not sensor_reader.connect():
            logger.error("Failed to connect to sensor")
            return False

        self.running = True

        # 센서 데이터 수집 스레드 시작
        sensor_thread = Thread(target=self._sensor_loop, daemon=True)
        sensor_thread.start()

        logger.info("SmartFarm System started")
        return True

    def _sensor_loop(self):
        """센서 데이터 수집 루프"""
        global current_data, sensor_history

        while self.running:
            try:
                # 센서 데이터 읽기
                data = sensor_reader.read_data()

                if data:
                    with data_lock:
                        current_data = data

                        # 히스토리에 추가
                        sensor_history.append({
                            'timestamp': datetime.fromtimestamp(data['timestamp']).isoformat(),
                            **data
                        })

                        # 히스토리 크기 제한
                        if len(sensor_history) > MAX_HISTORY:
                            sensor_history.pop(0)

                        # 데이터 파일에 저장
                        self._save_data(data)

                    # 자동 제어 처리
                    auto_controller.process_sensor_data(data)

                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error in sensor loop: {e}")
                time.sleep(1)

    def _save_data(self, data):
        """센서 데이터를 파일에 저장"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            data_file = f'../data/sensor_data_{date_str}.json'

            # 디렉토리 생성
            os.makedirs(os.path.dirname(data_file), exist_ok=True)

            # 데이터 추가 (append)
            with open(data_file, 'a') as f:
                record = {
                    'timestamp': datetime.fromtimestamp(data['timestamp']).isoformat(),
                    **data
                }
                f.write(json.dumps(record) + '\n')

        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def stop(self):
        """시스템 종료"""
        self.running = False
        sensor_reader.disconnect()
        auto_controller.cleanup()
        logger.info("SmartFarm System stopped")


# Flask 라우트
@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/sensor/current')
def get_current_sensor_data():
    """현재 센서 데이터 API"""
    with data_lock:
        if current_data:
            return jsonify({
                'success': True,
                'data': current_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No sensor data available'
            }), 404


@app.route('/api/sensor/history')
def get_sensor_history():
    """센서 데이터 히스토리 API"""
    with data_lock:
        return jsonify({
            'success': True,
            'data': sensor_history
        })


@app.route('/api/control/status')
def get_control_status():
    """제어 상태 API"""
    status = auto_controller.get_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/control/auto', methods=['POST'])
def set_auto_mode():
    """자동 모드 설정 API"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    auto_controller.set_auto_mode(enabled)

    return jsonify({
        'success': True,
        'message': f"Auto mode {'enabled' if enabled else 'disabled'}"
    })


@app.route('/api/control/manual', methods=['POST'])
def manual_control():
    """수동 제어 API"""
    data = request.get_json()
    device = data.get('device')
    state = data.get('state', False)

    if not device:
        return jsonify({
            'success': False,
            'message': 'Device not specified'
        }), 400

    auto_controller.manual_control(device, state)

    return jsonify({
        'success': True,
        'message': f"{device} turned {'ON' if state else 'OFF'}"
    })


@app.route('/api/thresholds', methods=['GET', 'POST'])
def manage_thresholds():
    """임계값 관리 API"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': auto_controller.THRESHOLDS
        })
    else:
        # POST - 임계값 업데이트
        data = request.get_json()
        for key, value in data.items():
            if key in auto_controller.THRESHOLDS:
                auto_controller.THRESHOLDS[key] = value

        return jsonify({
            'success': True,
            'message': 'Thresholds updated'
        })


def main():
    """메인 함수"""
    # 시리얼 포트 설정 (환경변수 또는 기본값)
    serial_port = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')

    # 스마트팜 시스템 초기화
    system = SmartFarmSystem(serial_port=serial_port)

    # 시스템 시작
    if not system.start():
        logger.error("Failed to start system")
        return

    try:
        # Flask 웹 서버 시작
        logger.info("Starting web server on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        system.stop()


if __name__ == '__main__':
    main()
