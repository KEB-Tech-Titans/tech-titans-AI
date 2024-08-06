#include <AFMotor.h>

// 28BYJ-48 스텝모터를 1번 포트 (M1과 M2)에 연결
AF_Stepper motor(48, 1);

void setup() {
  Serial.begin(9600);           // 9600 bps로 시리얼 통신 설정
  Serial.println("Stepper test!");

  motor.setSpeed(200);           // 모터 속도 설정 (RPM)

  // 초기 위치 설정
  Serial.println("Initializing motor position...");
  int initial_steps = 256; // 초기화 각도에 해당하는 스텝 수 (예: 45도)
  motor.step(initial_steps, FORWARD);
  Serial.println("Motor initialized to home position.");

  // 초기화 후 대기 메시지 출력
  Serial.println("Waiting Pass or Fail.");
}

void loop() {
  if (Serial.available() > 0) {
    String received_string = Serial.readStringUntil('\n');  // 새 줄이 올 때까지 읽기
    received_string.trim();  // 공백 제거

    // 입력에 따라 모터 제어
    if (received_string.equals("pass")) {
      Serial.println("Product has no defection!!!");
      Serial.println("Motor is going forward!!!");
      
      // 컨베이어에서 모터로 물체가 움직이는 시간 계산해서 delay집어넣을 것
      // 일단은 1초 대기
      delay(1000);
      motor.step(512, FORWARD);
      delay(2000);
      motor.step(512, BACKWARD);
    } else if (received_string.equals("fail")) {
      Serial.println("Product has defection!!!");
      Serial.println("Motor is going backward!!!");

      // 컨베이어에서 모터로 물체가 움직이는 시간 계산해서 delay 집어넣기
      delay(1000);
      motor.step(512, BACKWARD);
      delay(2000);
      motor.step(512, FORWARD);
    }

    // 명령 처리 후 대기 메시지 출력
    Serial.println("Waiting Pass or Fail.");
  }
}
