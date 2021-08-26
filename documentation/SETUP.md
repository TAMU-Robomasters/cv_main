# Setup

TLDR: install `nix`, run `commands/start`, and everything will be auto installed
<br>

### For Windows

* Get [WSL](https://youtu.be/av0UQy6g2FA?t=91) (Windows Subsystem for Linux) or [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10)<br>
    * If you're not familiar with WSL, I'd recommend [watching a quick thing on it like this one](https://youtu.be/av0UQy6g2FA?t=91)
    * Ubuntu 18.04 for WSL is preferred (same as in that linked video), but Ubuntu 20.04 or similar should work.
    * [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10) (just released August 2020) is needed if you want to use your GPU.<br>
* Once WSL is installed (and you have a terminal logged into WSL) follow the Mac/Linux instructions below.
* (protip: use the VS Code terminal instead of CMD when accessing WSL)

### For Mac/Linux

* Install [nix](https://nixos.org/guides/install-nix.html), more detailed guide [here](https://nixos.org/manual/nix/stable/#chap-installation)
    * Just run the following in your console/terminal app
        * `sudo apt-get update 2>/dev/null`
        * If you're on MacOS Big Sur
            *  see [this](https://duan.ca/2020/12/13/nix-on-macos-11-big-sur/) tutorial
        * If you're on MacOS Catalina, run:
            * `sh <(curl -L https://nixos.org/nix/install) --darwin-use-unencrypted-nix-store-volume `
        * If you're not, run:
            * `curl -L https://nixos.org/nix/install | bash`
        * `source $HOME/.nix-profile/etc/profile.d/nix.sh`
        * (may need to restart console/terminal)
* Install `git`
    * (if you don't have git just run `nix-env -i git`)
* Clone/Open the project
    * `cd wherever-you-want-to-save-this-project`<br>
    * `git clone https://github.com/TAMU-Robomasters/cv_main`
    * `cd *this-repo*`
* Actually run some code
    * run `commands/start` to get into the project environment
        * Note: this will almost certainly take a while the first time because it will auto-install exact versions of everything: `node`, `python`, `ruby`, all modules for them, etc
    * run `project commands` to list the project commands


# Basic Manual Setup (Alternative to Auto Setup)
* install python3
* install the pip modules in `requirements.txt`
* add the project directory to your `PYTHONPATH` env variable
* try running `python source/main.py`

# Advanced Setup

## Setup GPU-Acceleration and TensorRT (Optional)
### Install OpenCV
* Note: OpenCV must be compiled from source since the pip installable versions of OpenCV don't provide gpu support.
* First we need to install Cuda and Cudnn
    * If you are on a Jetson Product
        * Cuda and Cudnn is automatically installed once you flash the product.
    * If you are on Linux or WSL
        * If on WSL follow these steps first - https://docs.nvidia.com/cuda/wsl-user-guide/index.html#getting-started.
        * Download Cuda from https://developer.nvidia.com/cuda-downloads (You may need to make an Nvidia Developer Account).
        * Install Cuda
            * If on WSL follow https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#wsl-installation.
            * If on Ubuntu follow https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#ubuntu-installation.
        * Download Cudnn from https://developer.nvidia.com/cudnn (You may need to make an Nvidia Developer Account).
        * To install Cudnn follow https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html#installlinux.
* Add your cuda to PATH
    * `nano ~/.bashrc`.
    * Scroll all the way to the bottom and add the following:
        * `export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}`.
        * `export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}`.
* Before compiling OpenCV from source, uninstall pip's OpenCV using `pip3 uninstall opencv-contrib-python`.
* Open the scipt located at `cv_main/settings/commands/.install_opencv`.
* Modify the location of opencv installation, cuda arch bin version, and opencv_contrib_modules location
    * Location of OpenCV Installation - Personal Preference - This is to location where opencv and it's extra modules will be located.
    * Cuda Arch Bin version - Varies Per GPU - Set the arch bin version in the cmake command listed under `CUDA_ARCH_BIN`. See https://developer.nvidia.com/cuda-gpus and locate the version for your gpu. OpenCV will not compile if the version is incorrect.
    * OpenCV Extra Modules Path - Based on Location of OpenCV Installation - Set the extra modules path in the cmake command listed under `OPENCV_EXTRA_MODULES_PATH`. If you set the OpenCV install location to `~/Documents` then your path will look like `~/Documents/opencv_contrib/modules`.
* Navigate inside cv_main and run the script using `./settings/commands/.install_opencv`. If you face any errors, try running the commands sequentially and debug.
* To test some code change the gpu acceleration parameter in the `info.yaml` to  `gpu_acceleration: 1` and run test_main.

### Setup TensorRT
* Make sure you installed OpenCV from source as shown above.
* Install TensorRT Version 6+
    * If you are on Windows WSL you may face driver issues. I recommend switching to linux through dual boot.
    * If you are on a Jetson Product
        * TensorRT is automatically installed once you flash the product, only do the following steps if you are on an old version of tensorRT. You can check the version by running `dpkg -l | grep TensorRT`.
        * TensorRT cannot be installed normally. You must over-the-air (OTA) update the package or reflash with an updated SD Card Image. 
            * OTA Updates: https://docs.nvidia.com/jetson/archives/l4t-archived/l4t-3231/index.html#page/Tegra%2520Linux%2520Driver%2520Package%2520Development%2520Guide%2Fquick_start.html%23wwpID0EXHA.
            * Reflash: https://developer.nvidia.com/embedded/jetpack.
    * If you are on Linux
        * Download TensorRT version 6+ from https://developer.nvidia.com/tensorrt (You may need to make an Nvidia Developer Account).
        * Navigate to the directory where you downloaded TensorRT and delete any old packages you may have of TensorRT from the directory.
        * Open the script located at `./settings/commands/.install_tensorrt` and modify the `os` and `tag` based on your system and the version you installed. 
        * Run the script using `./settings/commands/.install_tensorrt`.
    * Add your cuda to PATH if you haven't already
        * `nano ~/.bashrc`.
        * Scroll all the way to the bottom and add the following:
            * `export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}`.
            * `export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}`.
* Install PyCuda by running `sudo pip3 install --global-option=build_ext --global-option="-I/usr/local/cuda/include" --global-option="-L/usr/local/cuda/lib64" pycuda`.
* Install Onnx by running `./settings/commands/.install_onnx`.
* Run the Makefile by navigating into `cv_main/source/modeling/plugins` and run `make`.
* Navigate to `cv_main/source/modeling/model`.
* Run `python3 yolo_to_onnx.py -m yolov4-tiny-416 --category_num 3` to convert from the current yolo model to an onnx model.
* Run `python3 onnx_to_tensorrt.py -m yolov4-tiny-416 --category_num 3` to convert from the generated onnx model to a TensorRT model.
* To test some code change the gpu acceleration parameter in the `info.yaml` to `gpu_acceleration: 2` and run test_main.
