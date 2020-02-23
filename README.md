# How to setup
1. install atk (single-line install all OSes) https://github.com/aggie-tool-kit/atk
2. install docker
For ubuntu 18.04 (bionic)
- `sudo apt-get update`
- `sudo apt-get remove docker docker-engine docker.io`
- `sudo apt install docker.io`
- `sudo systemctl start docker`
- `sudo systemctl enable docker`
For mac 
- `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
- `brew cask install docker`
- `open -a Docker --hide`
1. cd into the project (cv_main) directory
2. run `_ setup`. This command should install local dependencies and build the docker image

# How to run/test
run `_` to see all the avalible commands
run `_ test_main` to try running all the code on docker

# cv_main
cap = cv2.VideoCapture("nvcamerasrc ! video/x-raw(memory:NVMM), width=(int)1280, height=(int)720,format=(string)I420, framerate=(fraction)30/1 ! nvvidconv flip-method=0 ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
https://github.com/AlexeyAB/darknet

https://github.com/douglasrizzo/detection_util_scripts
