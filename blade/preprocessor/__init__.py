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

"""
BLADE's preprocessing engine for handling macros within the input data. Supports
control statements (#if, #else, #endif, etc.) as well as loops (#for, #endfor)
and file inclusion (#include).
"""

import re

from .. import reporting
report = reporting.get_report("preprocessor")

from .file import PreprocessorFile
from .scope import PreprocessorScope

class Preprocessor(object):
    """
    Holds the complete state of the preprocessor, including representations for
    every file in the scope. Used by the evaluation routines to resolve variables
    and included files.
    """

    def __init__(self):
        """Initialisation function for the preprocessor."""
        self.__scopes = {}

    @property
    def scopes(self):
        """Access all of the scopes defined within this Preprocessor instance"""
        return self.__scopes

    @property
    def all_files(self):
        """Access all of the files held within all defined scopes"""
        all_files = []
        for scope in self.scopes.values(): all_files += scope.files.values()
        return all_files

    def add_scope(self, name, deps=[], defines={}):
        """Create a new, empty scope with dependencies (contains no files)

        Args:
            name   : Name of the scope
            deps   : List of scopes that the new scope depends on (optional)
            defines: List of defined values to modify the preprocessor (optional)

        Returns:
            PreprocessorScope: The newly created scope object
        """
        if name in self.__scopes:
            raise Exception(report.error(f"Scope already exists for name {name}"))
        self.__scopes[name] = PreprocessorScope(name, deps, defines)
        return self.__scopes[name]

    def get_scope(self, name):
        """Return the scope for the requested key if it exist (else None).

        Args:
            name: Name of the scope to return

        Returns:
            PreprocessorScope: The requested scope object
        """
        return self.__scopes[name] if name in self.__scopes else None

    def add_file(self, scope, path, evaluated=False):
        """Add a file to an existing scope (does not immediately load the file)

        Args:
            scope    : The name of the scope to modify
            path     : The path to the file to add to the scope
            evaluated: File already evaluated, use for injecting programmatically
                       defined documents into the elaboration scope (default: False)

        Returns:
            PreprocessorFile: The newly created file object
        """
        if not scope in self.__scopes:
            raise Exception(report.error(f"Scope does not exist for name {scope}"))
        pre_file = PreprocessorFile(path, scope, self, evaluated=evaluated)
        self.__scopes[scope].add_file(path, pre_file)
        return pre_file

    def find_file(self, scope, file):
        """ Locate a pre-created PreprocessorFile object

        Find a file by searching through the associated scope, and then secondly
        any scopes the associated scope depends on. Works recursively to locate
        the file. If the file can't be found in the provided scope, then all
        depdencies of the scope will be searched as well.

        Args:
            scope: The name of the scope to search in
            file : The name of the file to locate

        Returns:
            PreprocessorFile: The located file object
        """
        if not scope in self.__scopes:
            return None
        elif self.__scopes[scope].get_file(file) != None:
            return self.__scopes[scope].get_file(file)
        else:
            found_file = None
            for dep in self.__scopes[scope].dependencies:
                if dep in self.__scopes and self.__scopes[dep].get_file(file):
                    found_file = self.__scopes[dep].get_file(file)
            return found_file

    def get_all_evaluated_files(self):
        """ Return all files from all scopes that have been successfully evaluated.

        Returns:
            list: List of PreprocessorFile objects.
        """
        all_evaluated = []
        for scope in self.__scopes:
            all_evaluated += [x for x in self.__scopes[scope].files.values() if x.evaluated]
        return all_evaluated
