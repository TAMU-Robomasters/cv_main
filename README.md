### How do I get this code to run?

Set [documentation/setup.md](https://github.com/TAMU-Robomasters/cv_main/blob/master/documentation/setup.md)

### What is this repo?

Its the home of all Tamu RoboMaster's cool code. (If you're looking for *boring* low-level C code you'll have to find the embedded teams repo)<br>
<br>

### How does the code work?

- `main/main.py` organizes everything
- `main/subsystems` are all the key components
- `./main/info.yaml` is our config. It is imported (indirectly) into basically every python file in the project
- everything in `main/` basically goes to the `main.py` or one of the tests in `main.py`
- everything in `toolbox/` is accessible to the python source code
