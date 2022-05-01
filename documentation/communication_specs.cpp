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
    long long magic_number = 0xdeadbeefdeadbef; // 1002855686552083439, is close to the max size of 9223372036854775807
    float horizontal_angle = 0.0;
    float vertical_angle   = 0.0;
    int should_shoot       = 0; // "int" encase we need to last-second cram some other data in during the competition
} message;

// read-message is probably as simple as: (assuming no interference)
//      memcpy((void*) &message, (const void *)&uart_buffer, sizeof(message))
