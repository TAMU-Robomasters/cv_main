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
    LOOK_AROUND = 0,
    LOOK_AT_COORDS = 1,
    FIRE = 2,
};

static constexpr uint8_t JETSON_MESSAGE_MAGIC = 'a';

struct JetsonMessage {
    uint8_t magic;           // 97
    float targetYawOffset;   // units=radians if target is to the left of camera-center, this will be negative
    float targetPitchOffset; // units=radians if target is below camera-center, this will be positive for some reason
    CVState cvState;         // 0 is LOOK_AROUND, 1 is LOOK_AT_COORDS, 2 is FIRE
} __attribute__((packed));

static_assert(sizeof(JetsonMessage) == 10);

// read-message is probably as simple as: (assuming no interference)
//      memcpy((void*) &message, (const void *)&uart_buffer, sizeof(message))
