# 하드웨어 연결 가이드

## 필요한 부품

### 아두이노 (센서 부분)
- Arduino Uno 또는 Nano (1개)
- DHT22 온습도 센서 (1개)
- pH 센서 모듈 (1개)
- 조도 센서 (CdS) (1개)
- 토양 수분 센서 (1개)
- 브레드보드 및 점퍼 케이블
- 10kΩ 저항 (CdS용)

### 라즈베리 파이 (제어 부분)
- Raspberry Pi 3/4 (1개)
- 5V 릴레이 모듈 3채널 (1개)
- 워터 펌프 12V (1개)
- LED 조명 스트립 12V (1개)
- 환풍기 12V (1개)
- 12V 전원 어댑터 (1개)

## 아두이노 연결도

### DHT22 온습도 센서
```
DHT22 VCC  → Arduino 5V
DHT22 DATA → Arduino Digital Pin 2
DHT22 GND  → Arduino GND
```

### pH 센서
```
pH Sensor VCC → Arduino 5V
pH Sensor OUT → Arduino Analog Pin A0
pH Sensor GND → Arduino GND
```

### 조도 센서 (CdS)
```
CdS 한쪽 → Arduino 5V
CdS 다른쪽 → Arduino A1 및 10kΩ 저항
10kΩ 저항 → Arduino GND
```

### 토양 수분 센서
```
Soil Sensor VCC → Arduino 5V
Soil Sensor OUT → Arduino Analog Pin A2
Soil Sensor GND → Arduino GND
```

### 시리얼 연결
```
Arduino USB → Raspberry Pi USB 포트
```

## 라즈베리 파이 GPIO 연결도

### 릴레이 모듈 (GPIO BCM 모드)
```
릴레이 VCC → Raspberry Pi 5V (Pin 2)
릴레이 GND → Raspberry Pi GND (Pin 6)

릴레이 IN1 (워터 펌프) → GPIO 17 (Pin 11)
릴레이 IN2 (LED 조명)  → GPIO 27 (Pin 13)
릴레이 IN3 (환풍기)    → GPIO 22 (Pin 15)
```

### 릴레이 출력 (12V 전원)
```
12V 전원 + → 각 릴레이 COM 단자
릴레이 NO → 워터 펌프 +
릴레이 NO → LED 조명 +
릴레이 NO → 환풍기 +

각 장치 - → 12V 전원 -
```

## 배선 주의사항

1. **전원 분리**: 아두이노와 라즈베리 파이는 각각 독립적인 전원 사용
2. **릴레이 전원**: 12V 장치는 반드시 별도 전원 어댑터 사용
3. **센서 전원**: 모든 센서는 아두이노 5V 사용 (라즈베리 파이 3.3V 아님)
4. **GND 공통**: 모든 장치의 GND는 공통으로 연결
5. **방수**: 토양 수분 센서와 워터 펌프는 방수 처리 필수

## GPIO 핀맵 (라즈베리 파이)

```
Physical Pin | BCM Pin | Function
-------------|---------|----------------
Pin 2        | 5V      | 릴레이 전원
Pin 6        | GND     | 릴레이 GND
Pin 11       | GPIO 17 | 워터 펌프 릴레이
Pin 13       | GPIO 27 | LED 조명 릴레이
Pin 15       | GPIO 22 | 환풍기 릴레이
```

## 센서 교정 방법

### pH 센서 교정
1. pH 7.0 표준 용액 준비
2. 센서를 용액에 담그고 전압 측정
3. `arduino/smartfarm_sensors.ino` 파일의 `PH_OFFSET` 값 조정
4. pH 4.0, 7.0, 10.0 용액으로 검증

### 토양 수분 센서 교정
1. 완전히 건조한 토양에서 값 측정 (최대값)
2. 물에 완전히 담근 상태에서 값 측정 (최소값)
3. `map()` 함수의 범위 값 조정

## 트러블슈팅

### 아두이노 연결 안됨
- USB 케이블 확인
- `/dev/ttyUSB0` 또는 `/dev/ttyACM0` 확인: `ls -l /dev/tty*`
- 권한 부여: `sudo usermod -a -G dialout $USER`

### 릴레이 작동 안됨
- GPIO 핀 번호 확인 (BCM vs Physical 모드)
- 릴레이 전원 확인 (5V)
- `gpio readall` 명령으로 핀 상태 확인

### 센서 값 이상
- 센서 전원 확인 (5V)
- 센서 연결 상태 확인
- 시리얼 모니터로 원시 데이터 확인
