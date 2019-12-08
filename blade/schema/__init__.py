# Copyright (C) 2019 Blu Wireless Ltd.
# All Rights Reserved.
#
# This file is part of BLADE.
#
# BLADE is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# BLADE is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# BLADE.  If not, see <https://www.gnu.org/licenses/>.
#

import inspect
import os
from pathlib import Path

# Import the tag base class manually
from .ph_tag_base import *

# Auto-magically import all schema files so they are exported as if in the root
# of the package.
schema_dir = Path(os.path.realpath(__file__)).parent
schema_py = [x for x in schema_dir.glob("ph_*.py")]

for schema_file in schema_py:
    # Load in the module contained in the file
    exec(f"from . import {schema_file.stem} as _")

    # Get all classes contained in the module and attach them to myself
    mod_classes = inspect.getmembers(_, inspect.isclass)
    for class_name, class_obj in mod_classes:
        globals()[class_name] = class_obj
