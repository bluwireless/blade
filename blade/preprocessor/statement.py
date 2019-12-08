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

import re

from .. import reporting
report = reporting.get_report("preprocessor.for_block")

from .common import evaluate_expression

class PreprocessorStatement(object):
    """
    Defines a statement that needs to be evaluated, for example an 'IF' condition
    where the evaluated result is returned and used to decide which section of
    code is included into the final file.
    """

    def __init__(self, line, regex, file):
        """ Initialisation function for a preprocessor statement

        Args:
            line : The raw line from the file to evaluate
            regex: The regular expression to use for this line
            file : Reference to the PreprocessorFile for looking up referenced
                   variables.
        """
        # Store initialisation variables
        self.__line  = line.strip()
        self.__regex = regex
        self.__file  = file
        # Evaluate the regular expression against the passed in line
        if self.__regex:
            matches = self.__regex.findall(self.__line)
            if len(matches) == 1:
                # Extract the type and (optional) condition from the result
                if isinstance(matches[0], tuple):
                    self.__type      = matches[0][0].lower()
                    self.__condition = matches[0][1] if len(matches[0]) > 1 else None
                else:
                    self.__type      = matches[0].lower()

    @property
    def line(self):
        """ Return the raw string this statement was derived from """
        return self.__line

    @property
    def type(self):
        """ Return the type of this statement (which regex was matched) """
        return self.__type

    @property
    def condition(self):
        """ Return the condition of this statement, i.e. what needs to be evaluated """
        return self.__condition

    def evaluate(self):
        """ Evaluate the statement and return the result.

        Evaluates the statement based on the extracted type and condition and
        returns a value. This could be true/false in the case of an IF statement,
        or it could be more complex like a key-value pair for a DEFINE statement.

        Returns:
            value: Depending on the type of statement this could be a primitive
                   value (string, integer, boolean) or a complex value which is
                   returned as a map.
        """
        if self.__type == 'include':
            parts = re.findall(r"^[\s]{0,}(?:\")?(.*?)(?:\")?[\s]{0,}$", self.__condition)
            if len(parts) == 0:
                raise Exception(report.error("Could not parse INCLUDE"))
            return parts[0]
        elif self.__type == 'define':
            parts = re.findall(r"^([A-Za-z0-9_-]{1,})[\s]{0,}(.*?)[\s]{0,}$", self.__condition)
            if len(parts) == 0:
                raise Exception(report.error("Could not parse DEFINE"))
            return {
                'key'  : parts[0][0],
                'value': parts[0][1] if (len(parts[0]) > 1) and (len(parts[0][1]) > 0) else True
            }
        elif self.__type == 'for':
            matches = re.findall(r"^(.*?) in (.*?)(?:[:])?[\s]{0,}$", self.__condition)
            if len(matches) == 0:
                raise Exception(report.error("Could not parse FOR condition"))
            # Extract the iterable part of the expression
            iterable = evaluate_expression(matches[0][1], self.__file)
            return { 'variable': matches[0][0], 'iterable': iterable }
        elif self.__type == 'ifdef':
            key = self.__condition.strip().split(' ')[0]
            return (self.__file.resolve_value(key) != None)
        elif self.__type == 'ifndef':
            key = self.__condition.strip().split(' ')[0]
            return (self.__file.resolve_value(key) == None)
        elif self.__type in ['if', 'elif']:
            return evaluate_expression(self.__condition, self.__file)
        elif self.__type == 'else':
            return True
        elif self.__type == 'endif':
            # NOTE: Special handling as 'endif' terminates a block
            return False
