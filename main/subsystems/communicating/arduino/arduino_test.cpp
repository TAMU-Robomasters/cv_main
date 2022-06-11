// nixpkgs.avrlibc
// nixpkgs.avrlibcCross
//

namespace Communication {
    struct MessageClass {
        uint64_t magic_number = 0xdeadbeefdeadbef; // 1002855686552083439, is close to the max size of 9223372036854775807
        float horizontal_angle = 0.0;
        float vertical_angle   = 0.0;
        uint8_t should_shoot   = 0; // "int" encase we need to last-second cram some other data in during the competition
    } __attribute__((packed)) message;
    
    int index = 0;
    char buffer[sizeof(MessageClass) * 2];
    char incoming_byte = '\0';
    
    bool messageIsReady() {
        if (Serial.available() > 0) {
            // read the incoming byte:
            incoming_byte = Serial.read();
            if (index < sizeof(buffer)) {
                buffer[index] = incoming_byte;
                ++index;
            }
        }
        
        if (index >= sizeof(buffer)) {
            index = 0;
            return true;
        }
        return false;
    }

    void sendMessage() {
        int bytesSent = Serial.write((char*)&message, sizeof(message));
    }
}


void setup() {
    // initialize digital pin LED_BUILTIN as an output.
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(9600);
}

void loop() {
  if (Communication::index == 0) {
    Communication::sendMessage();
  }
  
    if (Communication::messageIsReady()) {
        digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
        delay(1000);                       // wait for a second
        digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
        
        if (Communication::message.should_shoot != 0) {
            digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
            delay(1000);                       // wait for a second
            digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
        } else {
            digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
            delay(400);                       // wait for a second
            digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
            delay(400);                       // wait for a second
            digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
            delay(400);                       // wait for a second
            digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
            delay(400);                       // wait for a second
            digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
            delay(400);                       // wait for a second
            digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
        }
        
        Communication::message.should_shoot = 1;
        //    cout << "horizontal_angle = " << (Communication::message.horizontal_angle) << "\n";
        //    cout << "vertical_angle = " << (Communication::message.vertical_angle) << "\n";
        //    cout << "should_shoot = " << (Communication::message.should_shoot) << "\n";
    }
    delay(100);                        // wait for a second
    //  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
    //  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
}