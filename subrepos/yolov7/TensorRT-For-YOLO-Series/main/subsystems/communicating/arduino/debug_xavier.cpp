//void setup() {
//    // initialize digital pin LED_BUILTIN as an output.
//    pinMode(LED_BUILTIN, OUTPUT);
//    Serial.begin(115200);
//}

#include <SoftwareSerial.h>
SoftwareSerial MySerial(3, 4); // RX, TX

int incomingByte = 0; // for incoming serial data

void setup() {
  Serial.begin(115200); // opens serial port, sets data rate to 9600 bps
  MySerial.begin(115200); // opens serial port, sets data rate to 9600 bps
}

void loop() {
  // send data only when you receive data:
  if (MySerial.available() > 0) {
    // read the incoming byte:
    incomingByte = MySerial.read();
  }
  
  //Serial.println(incomingByte);
  // say what you got:
  //    Serial.print("I received: ");
  //Serial.write((char*)&incomingByte, sizeof(incomingByte));
  //Serial.println("Howdy");
  //Serial.println(incomingByte);
  
  if (MySerial.available() > 0) {
    //Serial.write((char*)&incomingByte, sizeof(incomingByte));
//    Serial.write(incomingByte, sizeof(incomingByte));
      Serial.println(incomingByte);
  }
}