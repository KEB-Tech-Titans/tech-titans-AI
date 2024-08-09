import serial
import time

# 시리얼 포트 설정 (올바른 포트 번호로 수정)

# 모터 아두이노 연결 코드
motor_port = 'COM8'  # 실제 포트에 맞게 설정
motor_baud_rate = 9600

# 컨베이어 아두이노 포트
conveyor_port = 'COM7'
conveyor_baud_rate = 9600

# 시리얼 포트 열기
motor_ser = serial.Serial(motor_port, motor_baud_rate, timeout=10)
time.sleep(2)  # 연결 안정화를 위해 잠시 대기

conveyor_ser = serial.Serial(conveyor_port, conveyor_baud_rate, timeout=10)
time.sleep(2)


def send_command(ser, command):
    ser.write(f"{command}\n".encode())         
    print(f"{command}")

def receive_command(ser, expected_data):
    while True:
        if ser.in_waiting > 0:
            received_data = ser.readline().decode().strip()
            print(f"{received_data}")
            if received_data == expected_data:
                return received_data
