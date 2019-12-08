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

from blade.preprocessor.scope import PreprocessorScope
from blade.preprocessor.file import PreprocessorFile

from ..common import gen_string, gen_fake_path, rand_value, rand_boolean
from random import randint
import os

## test_scope
#  Test that a scope can be created and its properties read back
#
def test_scope():
    # Create a random name
    name = gen_string(spaces=False)
    # Create some random defines
    defines = {}
    for i in range(randint(1, 20)):
        defines[gen_string(spaces=False)] = rand_value()
    # Create the scope
    scope = PreprocessorScope(name=name, deps=[], defines=defines)
    # Test reading back various properties
    assert scope.name == name
    # Check the defined values
    for key in defines.keys():
        assert key in scope.defines
        assert scope.defines[key] == defines[key]
    # Add some extra definitions
    for i in range(randint(1, 20)):
        key = gen_string(spaces=False)
        val = rand_value()
        scope.set_definition(key, val)
        assert key in scope.defines
        assert scope.defines[key] == val

## test_scope_files
#  Test creating a scope and attaching PreprocessorFile objects
#
def test_scope_files():
    # Create a scope
    scope = PreprocessorScope(name=gen_string(spaces=False))
    # Create a number of files
    files = []
    for i in range(randint(1, 20)):
        pre_file = PreprocessorFile(
            gen_fake_path(), scope, None, evaluated=rand_boolean()
        )
        files.append(pre_file)
        scope.add_file(pre_file.path, pre_file)
    # Check all files exist
    for pre_file in scope.files.values():
        assert pre_file in files
    # Check each file can be retrieved by full path and by the basename
    for pre_file in files:
        full_path_file = scope.get_file(pre_file.path)
        assert full_path_file == pre_file
        short_path_file = scope.get_file(os.path.basename(pre_file.path))
        assert short_path_file == pre_file
