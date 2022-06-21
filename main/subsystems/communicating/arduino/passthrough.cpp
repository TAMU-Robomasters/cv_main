#include <SoftwareSerial.h>

SoftwareSerial XavierSerial(2, 3); // RX, TX
SoftwareSerial DevSerial(4, 5);    // RX, TX

void setup() {
    // Open serial communications and wait for port to open:
    Serial.begin(115200);
    while (!Serial) {}; // wait for serial port to connect. Needed for Native USB only
    XavierSerial.begin(115200);
    DevSerial.begin(115200);
}

#define DEBUGGING // comment out to disable debugging


#ifdef DEBUGGING
    const auto xavier_prefix = "Xavier says: ";
    const auto dev_previx    = "Dev    says: ";
#endif


void loop() {
    if (XavierSerial.available()) {
        auto incoming_byte = XavierSerial.read();
        DevSerial.write((char*)&message, sizeof(message));
        
        #ifdef DEBUGGING
            Serial.write((char*)&xavier_prefix, sizeof(xavier_prefix));
            Serial.write((char*)&message, sizeof(message));
            Serial.println();
        #endif
    }
    
    if (DevSerial.available()) {
        auto incoming_byte = DevSerial.read();
        XavierSerial.write((char*)&message, sizeof(message));
        
        #ifdef DEBUGGING
            Serial.write((char*)&dev_previx, sizeof(dev_previx));
            Serial.write((char*)&message, sizeof(message));
            Serial.println();
        #endif
    }
}
