## Data Generation Module
This folder contains Maya-specific and general python code to generate training data. 

The training data is used to learn non-linear models that approximate complex character rigs.

### Directory structure:
1. **maya**: Maya-specific scripts for data generation, such as key framing, mesh exporters, rigging, mesh utilities, etc.
    * **animation**: Animation-related scripts.
        * ```key_frame_animation.py```: Utility class to generate keyframe poses for a given rig.
    * **generation**: Main data generation scripts.
        * ```pose_generator.py``: Script to generate poses and keyframes from user-defined parameters.
    * **io**: IO utilities.
        * ```abc_cmd.py```: Alembic exporter via scripting/command line.
        * ```fbx_cmd.py```: Fbx exporter via scripting/command line.
    * **rig**: Miscellaneous utility library to fetch and sample rig parameters and generate mesh instances (3d points) from rigs.
        * ```character_rig.py```: Functions to get, set and find rig parameters a.k.a. rig attributes.

2. **utils**: General-purpose utility functions that include statistics, math function, data readers and writers, etc.
    * **misc**: Miscellaneous functions.
        * ```math.py```: Math functions.

