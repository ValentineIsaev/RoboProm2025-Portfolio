#include <SoftwareSerial.h>

const int BOTTON_PIN = 4;
SoftwareSerial mySerial(0, 1);

const int xPin = A3; 

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  pinMode(BOTTON_PIN, INPUT_PULLUP);
  pinMode(xPin, INPUT);
}

void loop() {
  String return_but_state;
  
  if (Serial.available() > 0) { 
    String data = Serial.readStringUntil('\n');

    if (data != "NONE") {
       mySerial.println("S1 or S2");
    }
  }
  
  int xValue = analogRead(xPin);
  int buttonState = digitalRead(BOTTON_PIN);

   if (buttonState == LOW) {
    return_but_state = "1";
  } else {
    return_but_state = "0";
  }

  //mySerial.println(xValue); 
  String output = String(xValue) + "_" + return_but_state;

  Serial.println(output);
  delay(100);
}
