# Project

BLADE's project module drives the workflow for generating a DesignFormat description of the design from the raw YAML input. The workflow is broken down into 8 separate stages, each performing a specific transformation of the input data:

 1. Every file and folder provided by the user is searched to identify every available YAML file.
 2. The YAML description is passed through the preprocessor, starting from a specified top-level document.
 3. Output of the preprocessor is parsed into YAML tags, each of which is linked back to its source file.
 4. Definition of intrinsic types such as clock and reset are injected into the tag list.
 5. Every tag (including intrinsics) are validated to check that they are correct in terms of the schema (i.e. which tags can be attached as a child of another, what type an attribute can be, etc).
 6. Elaboration is performed for every tag described in the top-level YAML file, all contributing to a single DFProject instance.
 7. Automatic checks are executed against the DFProject instance produced by the elaboration stage.

## Usage
While BLADE comes with a command line interface which should meet most needs, it may be necessary to wrap the core within another tool. To enable this, the project module exposes the `build_project` which drives the workflow described above. The example below shows how to call the workflow:

```python
from blade import build_project
import json

dep_array = []

(df_project, violations) = build_project(
    top_file = '/path/to/my/top.yaml', # Path to the file to start elaboration from
    includes = [
        '/path/to/my/dependencies',    # Folders can be added to the search path...
        '/path/to/specific/file.yaml'  # along with specific files
    ],
    defines = {
        'MY_VAL' : 123,                # Integers, booleans, and strings can be
        'MY_BOOL': True,               # passed into the workflow. These are then
        'MY_STR' : 'hello!'            # exposed to the preprocessor.
    },
    max_depth  = None,                 # Controls depth of the elaboration (None means unlimited)
    en_convert = False,                # Enable conversions between tag types
    quiet      = False,                # Disables verbose messages and progress bars
    run_checks = True,                 # Enables rule checking on the elaborated design
    waivers    = [],                   # List of paths to waiver files for rule violations
    deps       = dep_array,            # Dependencies of the generated project can be recorded into a provided array
    profile    = False                 # Switches on execution time recording of each phase
)

if len(violations) > 0:
    print("WARNING: %i rule violations were raised" % len(violations))

with open('output.df_blob', 'w') as fh:
    fh.write(json.dumps(df_project.dumpObject()))
```

## API

```eval_rst
.. automodule:: blade.project
    :members:
    :undoc-members:
```