### How do I get this code to run?

Set [documentation/setup.md](https://github.com/TAMU-Robomasters/cv_main/blob/master/documentation/setup.md)

### What is this repo?

Its the home of all Tamu RoboMaster's cool code. (If you're looking for *boring* low-level C code you'll have to find the embedded teams repo)<br>
<br>

### How does the code work?

- `main/main.py` organizes everything
    - 1. It has a `setup()` function that outputs different runtime options (ex: fancy, straighforward, etc)
    - 2. The `setup()` () needs 5 main things to work though
        - See `main/_tests/test_main.py` for all of these in action
        - 1. `get_frame` (e.g. `setup(get_frame=a_function)`)
            - This function gets an image. This could be from a video file (for testing) or a live webcam feed
        - 2. `modeling` (e.g. `setup(modeling=a_module)`)
            - This one is a bit more complicated (see `./main/subsystems/modeling/modeling_main.py`) for an example
            - This essentially answers "what objects are inside this image?"
        - 3. `tracker` (e.g. `setup(tracker=a_module)`)
            - This one is simlar to modeling  (see `./main/subsystems/tracking/tracking_main.py`) for an example
            - This essentially answers "where are the objects now?" (higher efficiency than model)
        - 4. `aiming` (e.g. `setup(aiming=a_module)`)
            - This essentially answers "given the locations of obejcts, where should I aim?"
            - See `main/subsystems/aiming/aiming_main.py`
        - 5. `send_output` (e.g. `setup(send_output=a_function)`)
            - This is where we communicate either to the terminal (for testing) or to actual motors (when trying things for real)
            - See `main/subsystems/embedded_commmunication/embedded_main.py`
- `./main/info.yaml` is our config. It is imported (indirectly) into basically every python file in the project
- everything in `main/` basically goes to the `main.py` or one of the tests in `main.py`
- everything in `toolbox/` is accessible to the python source code
