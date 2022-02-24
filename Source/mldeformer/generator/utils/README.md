## Utility module
This folder contains IO, mesh, and miscellaneous utility functions.

### Directory structure:
1. **io**: A IO functions including data read and write, mesh write and write, and folder manipulation.
    * ```data_reader.py```: Functions for reading binary and json files.
    * ```data_writer.py```: Functions for writing out arrays to binary and json files as well as json strings to file.
    * ```mesh_reader.py```: Reads a mesh from file (only obj or ply formats supported).
    * ```mesh_writer.py```: Writes out a mesh to file (only obj and ply formats supported).
    * ```os_utils.py```: Functions for creating directories.
2. **mesh**: A colection of classes for mesh-related operations, such as error computation and mesh generation.
    * ```mesh_error.py```: Class that computes errrors and error heatmaps.
    * ```mesh_generator.py```: Class that generates meshes from 3D points.
3. **misc**: Miscellaneous functions to transform data structures and help the user do stuff.
    * ```data_converter.py```: Functions to convert numpy arrays into tensors and vice versa.
    * ```timer.py```: Runtime timer.
