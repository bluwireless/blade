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

from .. import reporting
report = reporting.get_report("preprocessor.block")

from .common import PreprocessorError
from .line import PreprocessorLine
from .statement import PreprocessorStatement

class PreprocessorBlock(object):
    """
    Represents a block of code within the file that is encased by some form of
    condition. This block can be optionally included, or replicated multiple times
    based on the outcome of evaluate the PreprocessorStatement.
    """

    def __init__(self, statement, file, lines=None):
        """ Initialisation function for a preprocessor block.

        Args:
            statement: PreprocessorStatement object that opens this block
            file     : Reference to the parent PreprocessorFile to resolve values
            lines    : Optionally provide the initial contents of this block
        """
        self.__statement = statement
        self.__file      = file
        self.__lines     = lines if lines != None else []

    @property
    def statement(self):
        """ Returns the statement opening this block """
        return self.__statement

    @property
    def file(self):
        """ Returns the file that contains this block """
        return self.__file

    def add_line(self, line):
        """ Append a new line to this block

        Args:
            line: The line to add which can be a PreprocessorLine, or a nested
                  PreprocessorBlock, or PreprocessorStatement.
        """
        if len([x for x in [PreprocessorLine, PreprocessorBlock, PreprocessorStatement] if isinstance(line, x)]) == 0:
            raise PreprocessorError(report.error(
                "Line not of type PreprocessorLine, PreprocessorBlock, or PreprocessorStatement"
            ), path=self.file.path)
        self.__lines.append(line)

    def evaluate(self):
        """ Evaluate all lines within this block and child blocks.

        Works through the stored lines, flattening out nested PreprocessorBlocks,
        evaluating PreprocessorStatements, and returning final array of lines.
        Note that this will throw exceptions if the evaluation fails to complete.

        Returns:
            list: A list of PreprocessorLines of the evaluated content
        """
        result = []
        for line in self.__lines:
            if isinstance(line, PreprocessorLine):
                result.append(line)
            elif isinstance(line, PreprocessorStatement):
                if line.type == 'define':
                    pair = line.evaluate();
                    self.__file.set_definition(pair['key'], pair['value'])
                elif line.type == 'include':
                    file = line.evaluate()
                    self.__file.include_file(file)
                    # NOTE: We preserve the include so that we can insert text
                    #       at the correct points in the output file.
                    result.append(line)
                else:
                    raise ValueError(report.error(
                        f"Unsupported PreprocessorStatement type: {line.type}"
                    ))
            elif isinstance(line, PreprocessorBlock):
                result += line.evaluate()
            else:
                raise ValueError(report.error("Line is of unknown type"))
        return result
