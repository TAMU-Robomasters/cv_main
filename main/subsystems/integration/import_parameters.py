from toolbox.globals import PARAMETERS

# import parameters from the info.yaml file
confidence            = PARAMETERS["model"]["confidence"]
threshold             = PARAMETERS["model"]["threshold"]
model_frequency       = PARAMETERS["model"]["frequency"]
hardware_acceleration = PARAMETERS['model']['hardware_acceleration']

model_fps             = PARAMETERS['aiming']['model_fps']
grid_size             = PARAMETERS['aiming']['grid_size']
stream_width          = PARAMETERS['aiming']['stream_width']
stream_height         = PARAMETERS['aiming']['stream_height']
framerate             = PARAMETERS['aiming']['stream_framerate']
horizontal_fov        = PARAMETERS['aiming']['horizontal_fov']
vertical_fov          = PARAMETERS['aiming']['vertical_fov']
std_buffer_size       = PARAMETERS['aiming']['std_buffer_size']
heat_buffer_size      = PARAMETERS['aiming']['heat_buffer_size']
rate_of_fire          = PARAMETERS['aiming']['rate_of_fire']
idle_counter          = PARAMETERS['aiming']['idle_counter']
std_error_bound       = PARAMETERS['aiming']['std_error_bound']
min_range             = PARAMETERS['aiming']['min_range']
max_range             = PARAMETERS['aiming']['max_range']
bullet_velocity       = PARAMETERS['aiming']['bullet_velocity']
length_barrel         = PARAMETERS['aiming']['length_barrel']
camera_gap            = PARAMETERS['aiming']['camera_gap']
barrel_camera_gap     = PARAMETERS['aiming']['barrel_camera_gap']
    
grab_frame            = PARAMETERS['videostream']['testing']['grab_frame']
record_interval       = PARAMETERS['videostream']['testing']['record_interval']
with_gui              = PARAMETERS['testing']['open_each_frame']
    
team_color            = PARAMETERS['embedded_communication']['team_color']
