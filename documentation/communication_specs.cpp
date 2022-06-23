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
struct {
    uint8_t magic_number   = 'a'; // 97
    float horizontal_angle = 0.0; // units=radians if target is to the left of camera-center, this will be negative
    float vertical_angle   = 0.0; // units=radians if target is below camera-center, this will be positive for some reason
    uint8_t status         = 0; // 0 is track, 1 is shoot, 2 is patrol
} __attribute__((packed));

// read-message is probably as simple as: (assuming no interference)
//      memcpy((void*) &message, (const void *)&uart_buffer, sizeof(message))
