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

import os

from .. import reporting
report = reporting.get_report("preprocessor.scope")

from .common import PreprocessorError

class PreprocessorScope(object):
    """
    Holds a scope of the preprocessor, containing its own files, defined values,
    and dependencies on other scopes.
    """

    def __init__(self, name, deps=None, defines=None):
        """ Initialisation function for the preprocessor scope

        Args:
            name   : The name of this scope
            deps   : The list of other scopes that this scope depends on
            defines: Mapping of defined values to modify parser behaviour
        """
        self.__name         = name
        self.__dependencies = deps if isinstance(deps, list) else []
        self.__files        = {}
        self.__defines      = dict(defines) if defines else {}
        # Allows register definitions to be detected
        self.set_definition('INCLUDE_REGISTERS', True)

    @property
    def name(self):
        """ Returns the name of the scope """
        return self.__name

    @property
    def dependencies(self):
        """ Returns the names of scopes that this scope depends upon """
        return self.__dependencies[:]

    @property
    def defines(self):
        """ Returns the map of defined values within this scope """
        return self.__defines

    @property
    def files(self):
        """ Returns the list of files held within this scope """
        return self.__files.copy()

    def add_dependency(self, dependency):
        """ Add a new dependency to this scope

        Args:
            dependency: The name of the dependency to add
        """
        self.__dependencies.append(dependency)

    def set_definition(self, key, value):
        """ Add a new key-value pair to the map of defined values

        Args:
            key  : The key for the definition
            value: The value for the definition
        """
        self.__defines[key] = value

    def add_file(self, file_path, pre_file):
        """ Add a new file to this scope, checks if it clashes with an existing file.

        Args:
            file_path: Path to this file on the filesystem
            pre_file : PreprocessorFile instance representing this file
        """
        file_name = os.path.basename(file_path)
        if file_name in self.__files:
            raise PreprocessorError(report.error(
                f"File {file_path} already exists in this scope: " +
                self.__files[file_name].path
            ), path=self.__files[file_name].path)
        # Attach the file to the scope
        self.__files[file_name] = pre_file

    def get_file(self, file_path):
        """ Return a file if it exists within the scope (else returns None)

        Args:
            file_path: Full or partial path to the file to find
        """
        file_path = os.path.basename(file_path)
        return self.__files[file_path] if file_path in self.__files else None
