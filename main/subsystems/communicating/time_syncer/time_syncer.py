from time import time as now
import math
from statistics import mean, stdev

class TimeSyncMessage: # FIXME: needs to be created out of C-objects
    magic_bytes = 0b00111011 # 8 bits (C++ char/C++ short int)
    def __init__(self):
        self.computer1_sent_time = 0
        self.computer2_receive_time = 0
        self.computer2_sent_time = 0
    
    @staticmethod
    def on_message_received(self, message):
        pass

class Communication:
    def __init__(self, message_class, acceptable_miliseconds_of_inaccuracy, max_history=1000, uart_info):
        self.acceptable_miliseconds_of_inaccuracy = acceptable_miliseconds_of_inaccuracy
        # FIXME: uart_info and create_port are just pseudocode here
        self.port = create_port(uart_info)
        self.prev_receive_time = 0
        self.prev_other_comp_sent_time = 0
        self.offsets = []
    
        # TODO: this might become a while loop depending on how things are implemented
        @port.on_receive
        def on_receive(message_bytes):
            # FIXME: message_bytes needs to be put into (e.g. cast) a Message structure 
            raw_message = cast(message_bytes, message_class) # FIXME
            right_now = self.prev_receive_time = now_in_miliseconds()
            self.prev_other_comp_sent_time = raw_message.raw_message.computer2_sent_time
            
            # 
            # record timing info
            # 
            if raw_message.computer1_sent_time: # if send->receive cycle (not just ->receive)
                internal_delay      = raw_message.computer2_sent_time - raw_message.computer2_receive_time
                loop_delay          = right_now - raw_message.computer1_sent_time
                communication_delay = loop_delay - internal_delay
                # communication_delay is here for logging, its (suprisingly) not actually needed for time sync
                
                # forward delay
                self.offsets.append(raw_message.computer1_sent_time - raw_message.computer2_receive_time)
                # backward delay
                self.offsets.append(right_now - raw_message.computer2_sent_time)
                # cap the size of the history
                self.offsets = self.offsets[:max_history]
            # 
            # handle init sync
            # 
            if self.still_initializing:
                # need enough samples to calculate a standard deviation
                amount_of_inaccuracy = get_confidence_width(self.offsets)
                if amount_of_inaccuracy < self.acceptable_miliseconds_of_inaccuracy:
                    # initalized! 
                    self.still_initializing = False
                else:
                    message = message_class()
                    # computer1=other and computer2=this_computer (eg: theyre backwards) for outgoing messages
                    message.computer1_sent_time    = self.prev_other_comp_sent_time
                    message.computer2_receive_time = self.prev_receive_time
                    message.computer2_sent_time = now_in_miliseconds()
                    port.send(bytes(message))
                    return # dont do any other computation until timing has been synced up
            else:
                average_offset = mean(self.offsets)
                # time is relative to this/local machine
                raw_message.sent_time = raw_message.computer2_sent_time + average_offset
                message_class.on_message_received(raw_message)
    
    def send_message(self, message):
        if self.still_initializing:
            print(f'''Warning: called .send_message() but communication was still initializing''')
            return
        # computer1=other and computer2=this_computer (eg: theyre backwards) for outgoing messages
        message.computer1_sent_time    = self.prev_other_comp_sent_time
        message.computer2_receive_time = self.prev_receive_time
        message.computer2_sent_time = now_in_miliseconds()
        self.port.send(bytes(message))

# 
# 
# helpers (TODO: probably should be moved into a toolbox file)
# 
# 
def now_in_miliseconds():
    return int(now()/1000)
    
def get_confidence_width(data, confidence_amount=0.95):
    sample_size = len(data)
    # not eough data to compute confidence bound
    if sample_size <= 3:
        return math.inf
    average_delay = mean(data)
    stdev_delay = stdev(data)
    stderr = stdev_delay / sample_size
    margin_of_error = stderr / 2
    # https://www.indeed.com/career-advice/career-development/how-to-calculate-confidence-interval
    return abs(confidence_amount*(stdev_delay / math.sqrt(sample_size)))