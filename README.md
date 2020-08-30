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
* WSL is installed (and you have a terminal logged into WSL) follow the Mac/Linux instructions below.

### For Mac/Linux

* Install [nix](https://nixos.org/guides/install-nix.html) 
    * Just run `sh <(curl -L https://nixos.org/nix/install) --daemon` in your console/terminal app
    * *Note:* you might need to close and reopen the your terminal after it installs
* Install `git`
    * run `nix-env -i git`
* Clone/Open the project
    * `cd wherever-you-want-to-save-this-project`<br>
    * `git clone https://github.com/TAMU-RoboMaster-Computer-Vision/cv_main`
    * `cd cv_main`
* Run the code
    * run `nix-shell`
        * Note: this will almost certainly take a while the first time because it will auto-install python, pip, a python virtual enviornment, and all of the pip modules that are needed.
    * run `commands` to see all of the project commands
    * run `python source/_tests/test_main.py` to try running the main program
