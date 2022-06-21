#include <SoftwareSerial.h>

// plug wire from pin 0 to pin 3 then use the serial monitor to verify this
// expect some problems with chars because arduino is processing both input and output

SoftwareSerial XavierSerial(3, 4); // RX, TX
SoftwareSerial DevSerial(5, 6);    // RX, TX

const auto baud = 115200;

void setup() {
    // Open serial communications and wait for port to open:
    Serial.begin(baud);
    XavierSerial.begin(baud);
    DevSerial.begin(baud);
}

#define DEBUGGING // comment out to disable debugging


#ifdef DEBUGGING
    int cycle = 0;
    const auto xavier_prefix = "Xavier says: ";
    const auto dev_previx    = "Dev    says: ";
#endif


void loop() {
    XavierSerial.listen(); // cant listen to DevSerial and XavierSerial at same time
    if (XavierSerial.available()) {
        char incoming_byte = XavierSerial.read();
        DevSerial.write(incoming_byte);
        
        #ifdef DEBUGGING
            Serial.write(xavier_prefix);
            Serial.write(incoming_byte);
            Serial.write('\n');
        #endif
    }
    
    if (DevSerial.available()) {
        char incoming_byte = DevSerial.read();
        XavierSerial.write(incoming_byte);
        
        #ifdef DEBUGGING
            Serial.write(dev_previx);
            Serial.write(incoming_byte);
            Serial.write('\n');
        #endif
    }
}
