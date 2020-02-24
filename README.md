# How to setup
1. install atk (single-line install all OSes) https://github.com/aggie-tool-kit/atk
2. install docker

   For Ubuntu 18.04 (bionic) <br>
   - `sudo apt-get update`
   - `sudo apt-get remove docker docker-engine docker.io`
   - `sudo apt install docker.io`
   - `sudo systemctl start docker`
   - `sudo systemctl enable docker`

   <br>
   For MacOS <br>
   
   - `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
   - `brew cask install docker`
   - `open -a Docker --hide`

   <br>
   For Windows 10 Home/Standard/Edu versions
   
   - See https://www.sitepoint.com/docker-windows-10-home/
   
   <br>
   For Windows 10 Pro/Enterprise
   
   - Get the official installer: https://www.docker.com/products/docker-desktop
3. cd into the project (cv_main) directory
4. run `_ setup`. This command should install local dependencies and build the docker image

# How do I run/test the project?
run `_` to see all the avalible commands
run `_ docker_test_main` to try running all the code on docker
run `_ local_test_main` to try running all the code with your local python

# How do I just run python?
If you just want to run a python file using your local python installation, use `_ local_python`. <br> Ex: `_ local_python source/main.py`
If you want to use the docker python do `_ docker_python`.

# Caveats/Gotcha's
- CV.showimg() and Matplotlib visuals don't work by default in docker because they open windows in docker instead of on your computer. There's ways to fix this (X11 forwarding) that I've been working on implementing.
- Same docker issue when importing info from the camera
- There could be docker issues connecting to the GPU (additional drivers) 

# Legacy readme
cap = cv2.VideoCapture("nvcamerasrc ! video/x-raw(memory:NVMM), width=(int)1280, height=(int)720,format=(string)I420, framerate=(fraction)30/1 ! nvvidconv flip-method=0 ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
https://github.com/AlexeyAB/darknet

https://github.com/douglasrizzo/detection_util_scripts
