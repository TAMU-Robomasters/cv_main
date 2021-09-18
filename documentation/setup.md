# Setup The Project Environment

### If you're an Experienced/Senior Dev

- (Don't git clone)
- Run this: `repo=https://github.com/TAMU-Robomasters/cv_main eval "$(curl -fsSL git.io/JE2Zm || wget -qO- git.io/JE2Zm)"`
- If you're on Windows, run it inside WSL (Ubuntu 20.04 preferably)
- If you're a responsible human being and therefore don't want run a sketchy internet script, props to you 👍. Take a look at the explaination below and you'll be able to run the commands yourself.

### If the above instructions didn't make sense

- Mac/Linux users
    - open up your terminal/console app
    - use `cd` to get to the folder where you want this project ([tutorial on how to use cd here](https://github.com/jeff-hykin/fornix/blob/b6fd3313beda4f80b7051211cb790a4f34da590a/documentation/images/cd_tutorial.gif))
    - (If you get errors on the next step -> keep reading)
    - Type this inside your terminal/console <br>`repo=https://github.com/TAMU-Robomasters/cv_main eval "$(curl -fsSL git.io/JE2Zm || wget -qO- git.io/JE2Zm)"`<br>[press enter]
    - Possible errors:
        - On MacOS, if your hard drive is encrypted on BigSur, you might need to [follow these steps](https://stackoverflow.com/questions/67115985/error-installing-nix-on-macos-catalina-and-big-sur-on-filevault-encrypted-boot-v#comment120393385_67115986)
        - On Linux, if you're running a *really* barebones system that somehow doesn't have either `curl` or `wget`, install curl or wget and rerun the previous step
- Windows users
    - Get [WSL](https://youtu.be/av0UQy6g2FA?t=91) (Windows Subsystem for Linux) or [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10)<br>
        - If you're not familiar with WSL, I'd recommend [watching a quick thing on it like this one](https://youtu.be/av0UQy6g2FA?t=91)
        - Ubuntu 18.04 for WSL is preferred (same as in that linked video), but Ubuntu 20.04 or similar should work.
        - [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10) (just released August 2020) is needed if you want to use your GPU.<br>
    - Once WSL is installed (and you have a terminal logged into WSL) follow the Mac/Linux instructions.
    - (tip: when accessing WSL, you probably want to use the VS Code terminal, or the [open source windows terminal](https://github.com/microsoft/terminal) instead of CMD)

<!-- 
Altertive instructions if GUI is needed (matplotlib, tkinter, qt, etc)

### For Windows

* Normally you just install [WSL](https://youtu.be/av0UQy6g2FA?t=91) and everything works, however the project uses a GUI and WSL doesn't like GUI's. <br>So there are a few options:
    1. You might just want to try manually installing everything (manual install details at the bottom)
    2. (Recommended) Install [virtualbox](https://www.virtualbox.org/wiki/Downloads) and setup Ubuntu 18.04 or Ubuntu 20.04
        - Here's [a 10 min tutorial](https://youtu.be/QbmRXJJKsvs?t=62) showing all the steps
        - Once its installed, boot up the Ubuntu machine, open the terminal/console app and follow the Linux instructions below
    3. Get WSL2 with Ubuntu, and use Xming
        - [Video for installing WSL2](https://www.youtube.com/watch?v=8PSXKU6fHp8)
        - If you're not familiar with WSL, I'd recommend [watching a quick thing on it like this one](https://youtu.be/av0UQy6g2FA?t=91)
        - [Guide for Using Xming with WSL2](https://memotut.com/en/ab0ecee4400f70f3bd09/)
        - (when accessing WSL, you probably want to use the VS Code terminal, or the [open source windows terminal](https://github.com/microsoft/terminal) instead of CMD)
        - [Xming link](https://sourceforge.net/projects/xming/?source=typ_redirect)
        - Once you have a WSL/Ubuntu terminal setup, follow the Linux instructions below
 
-->        

### What is that `eval` command doing?

1. Installing nix [manual install instructions here](https://nixos.org/guides/install-nix.html)
2. Installing `git` (using nix) if you don't already have git
3. It clones the repository
4. It `cd`'s inside of the repo
5. Then it runs `commands/start` to enter the project environment

After you've finished working and close the terminal, you can always return to project environment by doing
- `cd wherever-you-put-the-project`
- `commands/start`



# Manual Setup (Alternative to Project Environment)
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
