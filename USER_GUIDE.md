# 스마트팜 제어 시스템 사용 가이드

## 빠른 시작

### 1. 하드웨어 연결
`HARDWARE_SETUP.md` 파일을 참고하여 아두이노와 라즈베리 파이를 연결합니다.

### 2. 아두이노 펌웨어 업로드
1. Arduino IDE를 엽니다
2. `arduino/smartfarm_sensors.ino` 파일을 엽니다
3. DHT 센서 라이브러리 설치:
   - 도구 → 라이브러리 관리 → "DHT sensor library" 검색 및 설치
4. 아두이노 보드 연결 후 업로드

### 3. 라즈베리 파이 소프트웨어 설치
```bash
cd /home/user/web-aqua
chmod +x install.sh
./install.sh
```

### 4. 시스템 시작
```bash
# 수동 실행 (테스트용)
cd raspberry_pi
python3 main.py

# 또는 서비스로 실행
sudo systemctl start smartfarm
```

### 5. 웹 대시보드 접속
브라우저에서 `http://[라즈베리파이_IP]:5000` 접속

## 기능 설명

### 센서 모니터링
- **pH**: 토양 또는 수경재배 용액의 pH 측정
- **온도**: 환경 온도 (°C)
- **습도**: 상대 습도 (%)
- **조도**: 빛의 세기 (lux)
- **토양 수분**: 토양 수분 함량 (%)

### 자동 제어 기능
시스템은 다음 기준에 따라 자동으로 장치를 제어합니다:

| 조건 | 동작 |
|------|------|
| 온도 > 28°C | 환풍기 ON |
| 온도 < 26°C | 환풍기 OFF |
| 조도 < 300 lux | LED 조명 ON |
| 조도 ≥ 300 lux | LED 조명 OFF |
| 토양 수분 < 40% | 워터 펌프 ON |
| 토양 수분 ≥ 40% | 워터 펌프 OFF |
| pH < 5.5 또는 > 6.5 | 경고 알림 |

### 수동 제어
1. 웹 대시보드에서 "자동 모드" 토글을 OFF로 전환
2. 각 장치의 제어 버튼을 클릭하여 ON/OFF 제어
3. 자동 모드를 다시 ON으로 전환하면 자동 제어 재개

## 설정 변경

### 임계값 조정
`config.json` 파일을 편집하여 제어 기준값을 변경할 수 있습니다:

```json
{
  "thresholds": {
    "ph_min": 5.5,        // pH 최소값
    "ph_max": 6.5,        // pH 최대값
    "temp_min": 18.0,     // 온도 최소값
    "temp_max": 28.0,     // 온도 최대값
    "humidity_min": 60.0, // 습도 최소값
    "humidity_max": 80.0, // 습도 최대값
    "light_min": 300,     // 조도 최소값
    "soil_moisture_min": 40  // 토양 수분 최소값
  }
}
```

변경 후 서비스 재시작:
```bash
sudo systemctl restart smartfarm
```

### 시리얼 포트 변경
`config.json` 파일에서 시리얼 포트 설정 변경:

```json
{
  "serial": {
    "port": "/dev/ttyUSB0",  // 또는 /dev/ttyACM0
    "baudrate": 9600
  }
}
```

## 데이터 관리

### 센서 데이터 저장
센서 데이터는 자동으로 `data/` 디렉토리에 JSON 형식으로 저장됩니다:
- 파일명: `sensor_data_YYYY-MM-DD.json`
- 각 라인은 하나의 센서 데이터 레코드

### 로그 파일
시스템 로그는 `logs/smartfarm.log`에 저장됩니다.

## 트러블슈팅

### 문제: 센서 데이터가 표시되지 않음
**해결방법:**
1. 아두이노 연결 확인: `ls -l /dev/ttyUSB*` 또는 `ls -l /dev/ttyACM*`
2. 시리얼 권한 확인: `groups` 명령으로 dialout 그룹 포함 확인
3. 아두이노 시리얼 모니터로 데이터 출력 확인 (9600 baud)

### 문제: 릴레이가 작동하지 않음
**해결방법:**
1. GPIO 핀 연결 확인
2. 릴레이 전원 확인 (5V)
3. 수동으로 GPIO 테스트:
```bash
# GPIO 17 ON
echo "17" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio17/direction
echo "1" > /sys/class/gpio/gpio17/value
```

### 문제: 웹 대시보드 접속 안됨
**해결방법:**
1. 서비스 상태 확인: `sudo systemctl status smartfarm`
2. 포트 5000 사용 중인지 확인: `netstat -tlnp | grep 5000`
3. 방화벽 확인: `sudo ufw status`

### 문제: pH 센서 값이 부정확함
**해결방법:**
1. pH 표준 용액으로 센서 교정
2. `arduino/smartfarm_sensors.ino`의 `PH_OFFSET` 값 조정
3. 센서 전극 청소 및 보관액 확인

## API 엔드포인트

프로그래밍 방식으로 시스템을 제어하려면 다음 API를 사용하세요:

### 센서 데이터 조회
```bash
curl http://localhost:5000/api/sensor/current
```

### 자동 모드 설정
```bash
curl -X POST http://localhost:5000/api/control/auto \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### 수동 제어
```bash
curl -X POST http://localhost:5000/api/control/manual \
  -H "Content-Type: application/json" \
  -d '{"device": "water_pump", "state": true}'
```

## 유지보수

### 정기 점검 항목
- [ ] 센서 청소 (주 1회)
- [ ] pH 센서 교정 (월 1회)
- [ ] 워터 펌프 필터 청소 (월 1회)
- [ ] 시스템 로그 확인 (주 1회)
- [ ] 데이터 백업 (월 1회)

### 센서 수명
- pH 센서: 6개월~1년 (사용 빈도에 따라)
- DHT22: 2~3년
- 토양 수분 센서: 1~2년 (부식 방지 처리 필요)

## 고급 기능

### 데이터 분석
저장된 센서 데이터를 Python으로 분석:

```python
import json

# 데이터 읽기
with open('data/sensor_data_2025-01-01.json', 'r') as f:
    data = [json.loads(line) for line in f]

# 평균 온도 계산
avg_temp = sum(d['temperature'] for d in data) / len(data)
print(f"Average temperature: {avg_temp:.1f}°C")
```

### 알림 설정
시스템 알림을 이메일이나 SMS로 받으려면 `raspberry_pi/main.py`에 알림 기능 추가

### 원격 접속
외부에서 접속하려면 포트 포워딩 또는 VPN 설정 필요

## 문의 및 지원
- GitHub Issues: [프로젝트 저장소 URL]
- 이메일: [이메일 주소]
