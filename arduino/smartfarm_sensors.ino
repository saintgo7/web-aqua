/*
 * 스마트팜 센서 제어 시스템
 * Arduino UNO/Nano 호환
 *
 * 센서 목록:
 * - pH 센서 (아날로그 A0)
 * - DHT22 온습도 센서 (디지털 2번 핀)
 * - 조도 센서 CdS (아날로그 A1)
 * - 토양 수분 센서 (아날로그 A2)
 */

#include <DHT.h>

// 핀 정의
#define DHTPIN 2          // DHT22 데이터 핀
#define DHTTYPE DHT22     // DHT 센서 타입
#define PH_PIN A0         // pH 센서 핀
#define LIGHT_PIN A1      // 조도 센서 핀
#define SOIL_PIN A2       // 토양 수분 센서 핀

// DHT 센서 초기화
DHT dht(DHTPIN, DHTTYPE);

// pH 센서 보정값
const float PH_OFFSET = 0.0;  // 보정값 (교정 필요)
const float PH_SLOPE = 3.5;   // pH 단위당 전압 변화

// 측정 간격 (밀리초)
const unsigned long MEASURE_INTERVAL = 2000;
unsigned long lastMeasureTime = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();

  // 아날로그 핀 설정
  pinMode(PH_PIN, INPUT);
  pinMode(LIGHT_PIN, INPUT);
  pinMode(SOIL_PIN, INPUT);

  Serial.println("Smart Farm Sensor System Started");
  Serial.println("Format: pH,Temperature,Humidity,Light,SoilMoisture");
}

void loop() {
  unsigned long currentTime = millis();

  // 설정된 간격마다 센서 읽기
  if (currentTime - lastMeasureTime >= MEASURE_INTERVAL) {
    lastMeasureTime = currentTime;

    // 센서 데이터 읽기
    float ph = readPH();
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int lightLevel = readLight();
    int soilMoisture = readSoilMoisture();

    // 데이터 유효성 검사
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("ERROR: DHT sensor reading failed");
      return;
    }

    // CSV 형식으로 데이터 전송
    Serial.print(ph, 2);
    Serial.print(",");
    Serial.print(temperature, 1);
    Serial.print(",");
    Serial.print(humidity, 1);
    Serial.print(",");
    Serial.print(lightLevel);
    Serial.print(",");
    Serial.println(soilMoisture);
  }

  // 시리얼 명령 처리
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
}

// pH 센서 읽기
float readPH() {
  int sensorValue = analogRead(PH_PIN);
  float voltage = sensorValue * (5.0 / 1024.0);

  // pH 값 계산 (센서별로 교정 필요)
  // 일반적인 pH 센서: pH 7.0에서 약 2.5V
  float ph = 7.0 - ((voltage - 2.5) / PH_SLOPE) + PH_OFFSET;

  // pH 범위 제한 (0-14)
  if (ph < 0) ph = 0;
  if (ph > 14) ph = 14;

  return ph;
}

// 조도 센서 읽기 (0-1023, 높을수록 어두움)
int readLight() {
  int sensorValue = analogRead(LIGHT_PIN);
  // 밝기로 변환 (0-1023을 0-1000 lux로 근사)
  int lightLevel = map(1023 - sensorValue, 0, 1023, 0, 1000);
  return lightLevel;
}

// 토양 수분 센서 읽기 (0-100%)
int readSoilMoisture() {
  int sensorValue = analogRead(SOIL_PIN);
  // 수분 퍼센트로 변환 (센서별 보정 필요)
  // 일반적으로 물에 담그면 낮은 값, 건조하면 높은 값
  int moisture = map(sensorValue, 1023, 0, 0, 100);

  // 범위 제한
  if (moisture < 0) moisture = 0;
  if (moisture > 100) moisture = 100;

  return moisture;
}

// 시리얼 명령 처리
void processCommand(String command) {
  command.trim();

  if (command == "STATUS") {
    Serial.println("OK: Sensor system running");
  }
  else if (command == "RESET") {
    Serial.println("OK: System reset");
    // 소프트웨어 리셋 (아두이노 재시작)
    asm volatile ("  jmp 0");
  }
  else if (command.startsWith("CALIBRATE_PH:")) {
    // pH 보정 명령 처리 (향후 구현)
    Serial.println("OK: pH calibration mode");
  }
  else {
    Serial.println("ERROR: Unknown command");
  }
}
