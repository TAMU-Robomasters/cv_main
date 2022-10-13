### How do I get this code to run?

Set [documentation/setup.md](https://github.com/TAMU-Robomasters/cv_main/blob/master/documentation/setup.md)

### What is this repo?

Its the home of all Tamu RoboMaster's cool code. (If you're looking for *boring* low-level C code you'll have to find the embedded teams repo)<br>
<br>

### How does the code work?

- `main/main.py` is only ~12 lines of code
     - These are the 3 core functions in the codebase:
     - `model.when_frame_arrives()`
     - `aim.when_bounding_boxes_refresh()`
     - `communicate.when_aiming_refreshes()`
- Everything outside of those functions are just helpers for those functions 
- If you need to set a constant (like IMAGE_DIMENSIONS) do it in the `./main/info.yaml`
- If a tool/function is generic (used in multiple places) put it in the toolbox folder
