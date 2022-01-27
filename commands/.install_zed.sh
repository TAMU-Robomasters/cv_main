#!/usr/bin/env bash

# ASSUMES Python 3.6+ and Python OpenCV Installed

# Instructions for Jetson: https://www.stereolabs.com/docs/installation/jetson/
# Installation Versions: https://www.stereolabs.com/developers/release/

# Install Dependencies
pip3 install Cython
pip3 install PyOpenGL PyOpenGL_accelerate

# Install Zed SDK 3.6.1 for Jetpack 4.5, accept all options
# If not on Jetpack 4.5, use the following commented lines to check the jetpack version
# If not on Jetpack 4.5, and you found the jetpack version, go to https://www.stereolabs.com/developers/release/ to find respective link

# git clone https://github.com/jetsonhacks/jetsonUtilities
# cd jetsonUtilities
# python3 jetsonInfo.py

cd ~/Downloads
wget https://download.stereolabs.com/zedsdk/3.6/jp45/jetsons
chmod +x jetsons
./jetsons

# Update bashrc
echo 'export OPENBLAS_CORETYPE=ARMV8' >> ~/.bashrc
source ~/.bashrc