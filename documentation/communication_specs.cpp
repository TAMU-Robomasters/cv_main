// 
// port specs
// 
    // baudrate = 115200
    // bytesize = serial.EIGHTBITS
    // parity   = serial.PARITY_NONE
    // stopbits = serial.STOPBITS_ONE

// 
// message specs
// 
enum CVState : uint8_t {
    LOOK_AT_COORDS = 0,
    FIRE = 1,
    LOOK_AROUND = 2,
};

static constexpr uint8_t JETSON_MESSAGE_MAGIC = 'a';

struct JetsonMessage {
    uint8_t magic;           // 97
    float targetYawOffset;   // units=radians if target is to the left of camera-center, this will be negative
    float targetPitchOffset; // units=radians if target is below camera-center, this will be positive for some reason
    CVState cvState;         // 0 is LOOK_AT_COORDS, 1 is FIRE, 2 is LOOK_AROUND
} __attribute__((packed));

// read-message is probably as simple as: (assuming no interference)
//      memcpy((void*) &message, (const void *)&uart_buffer, sizeof(message))
