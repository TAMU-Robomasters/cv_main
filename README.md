## How to setup (The not-recommended-but-simple-to-explain way)
* install python3
* install the pip modules in `requirements.txt`
* add the project directory to your `PYTHONPATH` env variable
* try running `python source/main.py`

# How to setup (Prefered way)

### For Windows

* Get [WSL](https://youtu.be/av0UQy6g2FA?t=91) (Windows Subsystem for Linux) or [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10)<br>
    * If you're not familiar with WSL, I'd recommend [watching a quick thing on it like this one](https://youtu.be/av0UQy6g2FA?t=91)
    * Ubuntu 18.04 for WSL is preferred (same as in that linked video), but Ubuntu 20.04 or similar should work.
    * [WSL2](https://www.omgubuntu.co.uk/how-to-install-wsl2-on-windows-10) (just released August 2020) is needed if you want to use your GPU.<br>
* Once WSL is installed (and you have a terminal logged into WSL) follow the Mac/Linux instructions below.

### For Mac/Linux

* Install [nix](https://nixos.org/guides/install-nix.html) (in case something goes wrong; here's the [original instructions](https://nixos.org/manual/nix/stable/#chap-installation))
    * Just run the following in your console/terminal app
        * `sudo apt-get update 2>/dev/null`
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
    * `git clone https://github.com/TAMU-RoboMaster-Computer-Vision/cv_main`
    * `cd cv_main`
* Actually run some code
    * run `nix-shell` to get into the project enviornment
        * Note: this will almost certainly take a while the first time because it will auto-install exact versions of everything: `python`, `pip`, the python virtual enviornment, all of the pip modules, and auto-setup the env variables like the PYTHONPATH.
    * run `commands` to see all of the project commands
    * run `python source/_tests/test_main.py` to try running the main program

## Setup GPU-Acceleration and TensorRT (Optional)
### Install OpenCV
* Note: OpenCV must be compiled from source since the pip installable versions of OpenCV don't provide gpu support
* Open the scipt located at `cv_main/settings/commands/.install_opencv`
* Modify the location of opencv installation, cuda arch bin version, and opencv_contrib_modules location
    * Location of OpenCV Installation - Personal Preference - This is to location where opencv and it's extra modules will be located
    * Cuda Arch Bin version - Varies Per GPU - Set the arch bin version in the cmake command listed under `CUDA_ARCH_BIN`. See https://developer.nvidia.com/cuda-gpus and locate the version for your gpu. OpenCV will not compile if the version is incorrect.
    * OpenCV Extra Modules Path - Based on Location of OpenCV Installation - Set the extra modules path in the cmake command listed under `OPENCV_EXTRA_MODULES_PATH`. If you set the OpenCV install location to `~/Documents` then your path will look like `~/Documents/opencv_contrib/modules`
* Navigate inside cv_main and run the script using `./settings/commands/.install_opencv`. If you face any errors, try running the commands sequentially and debug.

### Install TensorRT
* If you are on a Jetson Product
    * TensorRT cannot be installed normally. You must over-the-air (OTA) update the package or reflash with an updated SD Card Image. 
        * OTA Updates: https://docs.nvidia.com/jetson/archives/l4t-archived/l4t-3231/index.html#page/Tegra%2520Linux%2520Driver%2520Package%2520Development%2520Guide%2Fquick_start.html%23wwpID0EXHA
        * Reflash: https://developer.nvidia.com/embedded/jetpack
* If you are on Linux
    * Ensure no previous versions of tensorRT are installed by navigating inside cv_main and running `./settings/commands/uninstall_tensorrt`
