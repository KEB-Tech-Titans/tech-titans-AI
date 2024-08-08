import serial
import time

# 시리얼 포트 설정 (올바른 포트 번호로 수정)

# 모터 아두이노 연결 코드
motor_port = 'COM8'  # 실제 포트에 맞게 설정
motor_baud_rate = 9600

# 시리얼 포트 열기
ser = serial.Serial(motor_port, motor_baud_rate, timeout=10)
time.sleep(2)  # 연결 안정화를 위해 잠시 대기

def send_command(command):
    ser.write(f"{command}\n".encode())         
    print(f"Sent to Arduino: {command}")

def control_motor(ser, product_status):
    try:
        while True:
            if ser.in_waiting > 0:
                arduino_data = ser.readline().decode().strip()
                print(f"Arduino: {arduino_data}")

                # 제품이 감지되었을 때 응답
                if "Waiting Pass or Fail." in arduino_data:
                    # 제품 상태를 판단하는 로직
                    send_command(product_status)

            time.sleep(1)  # 1초 대기

    except KeyboardInterrupt:
        print("종료합니다.")

    finally:
        ser.close()  # 시리얼 포트 닫기
