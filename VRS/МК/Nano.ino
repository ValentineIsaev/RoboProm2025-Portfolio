#include <Servo.h>
#include <SoftwareSerial.h>

const int ECHO_PIN = 4;   
const int TRIG_PIN = 3;  
Servo myServo;            
SoftwareSerial mySerial(10, 11); 

int lastServoPosition = -1; 

void setup() {
  myServo.attach(9);
  Serial.begin(9600); 
  mySerial.begin(9600); 

  pinMode(TRIG_PIN, OUTPUT); 
  pinMode(ECHO_PIN, INPUT);  
}

void loop() {
  long duration, distance;
  String output; 

  if (Serial.available() > 0) { 
    String data = Serial.readStringUntil('\n'); 

    int commaIndex = data.indexOf('_'); 
    
    if (commaIndex != -1) { 
      String joystick = data.substring(0, commaIndex); 
      String is_botton = data.substring(commaIndex + 1); 
      
      int xValue = joystick.toInt(); 
      int servoPosition = map(xValue, 0, 1023, 0, 180);  

      myServo.write(servoPosition); 
      delay(15); 

      //mySerial.println(is_botton); 
      if (is_botton == "_1") {
        digitalWrite(TRIG_PIN, LOW);
        delayMicroseconds(2);
        digitalWrite(TRIG_PIN, HIGH);
        delayMicroseconds(10);
        digitalWrite(TRIG_PIN, LOW);

        duration = pulseIn(ECHO_PIN, HIGH); 
        distance = (duration * 0.0344) / 2; 
        output = String(distance);
      } else {
        output = "NONE"; 
      }

      Serial.println(output); 
    }
  }
}
