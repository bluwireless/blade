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

# Auto-magically import all rules from files in this folder
checkers_dir = Path(os.path.realpath(__file__)).parent
checkers_py  = [x for x in checkers_dir.glob("*.py") if not "__init__.py" in x.name]

# Look for all functions starting "check_" and list them
all_checks = []
for checker in checkers_py:
    # Load in the module contained in the file
    exec(f"from . import {checker.stem} as _")

    # Get all functions
    functions = inspect.getmembers(_, inspect.isfunction)

    # Filter out just the functions starting with "check_"
    all_checks += [x for x in functions if x[0].startswith("check_")]

def get_all_checkers():
    """ Return all of the check routines discovered in this directory

    Returns:
        list: List of tuples containing name of the check and the function
    """
    return all_checks
