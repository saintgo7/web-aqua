#!/bin/bash

# 스마트팜 제어 시스템 설치 스크립트
# Raspberry Pi용

echo "==================================="
echo "스마트팜 제어 시스템 설치"
echo "==================================="

# 시스템 업데이트
echo "[1/6] 시스템 업데이트 중..."
sudo apt-get update

# Python3 및 pip 설치
echo "[2/6] Python3 및 필수 패키지 설치 중..."
sudo apt-get install -y python3 python3-pip python3-dev git

# Python 라이브러리 설치
echo "[3/6] Python 라이브러리 설치 중..."
pip3 install -r requirements.txt

# 시리얼 포트 권한 설정
echo "[4/6] 시리얼 포트 권한 설정 중..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G gpio $USER

# 필요한 디렉토리 생성
echo "[5/6] 디렉토리 생성 중..."
mkdir -p data logs

# systemd 서비스 파일 생성
echo "[6/6] 시스템 서비스 설정 중..."
cat > /tmp/smartfarm.service << EOF
[Unit]
Description=SmartFarm Control System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)/raspberry_pi
ExecStart=/usr/bin/python3 $(pwd)/raspberry_pi/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/smartfarm.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "==================================="
echo "설치 완료!"
echo "==================================="
echo ""
echo "다음 명령어를 사용하세요:"
echo ""
echo "  # 서비스 시작"
echo "  sudo systemctl start smartfarm"
echo ""
echo "  # 서비스 상태 확인"
echo "  sudo systemctl status smartfarm"
echo ""
echo "  # 부팅 시 자동 시작 설정"
echo "  sudo systemctl enable smartfarm"
echo ""
echo "  # 수동 실행 (테스트용)"
echo "  cd raspberry_pi && python3 main.py"
echo ""
echo "웹 대시보드: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "주의: 시리얼 권한 적용을 위해 재로그인 또는 재부팅이 필요할 수 있습니다."
echo ""
