  #include <avr/sleep.h>

  //제품 초기 인식
  #define TRIG 10 //TRIG 핀 설정 (초음파 보내는 핀)
  #define ECHO 11 //ECHO 핀 설정 (초음파 받는 핀)

  //불량품 제거 인식
  #define TRIG_ 6 //6 //TRIG 핀 설정 (초음파 보내는 핀)
  #define ECHO_ 7 //7 //ECHO 핀 설정 (초음파 받는 핀)

  #define SENSE 12 //12 //제품 감지 LED 등
  #define SENSE_ 13 //13 //이동 감지 LED 등

  #define CONVEYOR 3

  bool bObject = false;
  bool bBad = false;

  bool bPass = false;

  void setup() {

    Serial.begin(9600); //PC모니터로 센서값을 확인하기위해서 시리얼 통신을 정의해줍니다. 
                        //시리얼 통신을 이용해 PC모니터로 데이터 값을 확인하는 부분은 자주사용되기 때문에
                        //필수로 습득해야하는 교육코스 입니다.
    Serial.setTimeout(10);

    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);

    pinMode(TRIG_, OUTPUT);
    pinMode(ECHO_, INPUT);

    pinMode(SENSE, OUTPUT);
    pinMode(SENSE_, OUTPUT);

    pinMode(CONVEYOR, OUTPUT);

  }



  void loop()
  {
    bPass = false;

    long duration, distance;
    long duration_, distance_;

    digitalWrite(TRIG, LOW);
    digitalWrite(TRIG_, LOW);
    delayMicroseconds(2);

    digitalWrite(TRIG, HIGH);
    digitalWrite(TRIG_, HIGH);
    delayMicroseconds(10);

    digitalWrite(TRIG, LOW);
    digitalWrite(TRIG_, LOW);

    duration = pulseIn (ECHO, HIGH); //물체에 반사되어돌아온 초음파의 시간을 변수에 저장합니다.
    duration_ = pulseIn (ECHO_, HIGH); //물체에 반사되어돌아온 초음파의 시간을 변수에 저장합니다.

    //34000*초음파가 물체로 부터 반사되어 돌아오는시간 /1000000 / 2(왕복값이아니라 편도값이기때문에 나누기2를 해줍니다.)

    //초음파센서의 거리값이 위 계산값과 동일하게 Cm로 환산되는 계산공식 입니다. 수식이 간단해지도록 적용했습니다.

    distance = duration * 17 / 1000; 

    distance_ = duration_ * 17 / 1000 + 1; 

    //PC모니터로 초음파 거리값을 확인 하는 코드 입니다.


    //Serial.println(duration_ ); //초음파가 반사되어 돌아오는 시간을 보여줍니다.
    Serial.print("Product Distance_ : ");
    Serial.print(distance_); //측정된 물체로부터 거리값(cm값)을 보여줍니다.
    Serial.print(" Cm,   ");
    
    // LOW -> 출발, HIGH -> 멈춤
    // 물체가 센서에 닿았을떄 -> 물체 인식 -> 영상 촬영
    if(distance < 10)
    {
        bObject = true;

        Serial.println("Product Sensing...");

        digitalWrite(SENSE, HIGH);
        digitalWrite(CONVEYOR, HIGH);
        delay(1000);

        Serial.println("Captured Frame");
        digitalWrite(CONVEYOR, LOW);
        delay(2000);
    }
    else
    {
      bObject = false;    
      digitalWrite(SENSE, LOW);
      digitalWrite(CONVEYOR, LOW);
    }



    //Serial.println(duration ); //초음파가 반사되어 돌아오는 시간을 보여줍니다.
    Serial.print("Move Distance : ");
    Serial.print(distance); //측정된 물체로부터 거리값(cm값)을 보여줍니다.
    Serial.println(" Cm");

    // 분석이 끝나면 컴퓨터 -> 컨베이어벨트로 분석 완료 신호를 보냄
    String str = Serial.readString();
    str.trim();
    
    if(distance_ < 10 && !bObject)
    {
      bBad = true;

      Serial.println("Waiting process...");
      digitalWrite(SENSE_, HIGH);
      digitalWrite(CONVEYOR, HIGH);

      if(str.compareTo("end") == 0)
      {
        Serial.println("Analyzing Finished");
        digitalWrite(SENSE_, LOW);
        digitalWrite(CONVEYOR, LOW);
      }
    }
    else
    {

      bBad = false;

      if(!bObject)
      {
        digitalWrite(SENSE_, LOW);
        digitalWrite(CONVEYOR, LOW);
      }

    }

    delay(1000); //1초마다 측정값을 보여줍니다.

  }