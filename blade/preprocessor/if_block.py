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

from .block import PreprocessorBlock

from .. import reporting
report = reporting.get_report("preprocessor.if_block")

from .common import PreprocessorError

class PreprocessorIfBlock(PreprocessorBlock):
    """
    Represents a series of blocks of code encased in a 'if-elif-else' relationship
    evaluating to only return the valid section. The block itself does not contain
    any lines, but adding a line will append it to the last active block (e.g.
    whichever if/elif/else section was last added).
    """

    def __init__(self, file):
        """
        Initialisation function for a preprocessor IF block. Unlike the parent
        class constructor, passing a statement is not required.

        Args:
            file: Reference to the PreprocessorFile to resolve values.
        """
        super().__init__(None, file)
        self.__file     = file
        self.__sections = []

    def add_section(self, statement):
        """ Append a new if/elif/else section to the IF block.

        Note that the statement is contained within the PreprocessorBlock in the
        section.

        Args:
            statement: The PreprocessorStatement opening the section
        """
        # Perform some sanity checks
        if statement.type == 'if' and len(self.__sections) > 0:
            raise ValueError(report.error(
                "Attempted to add second 'IF' statement to block"
            ))
        elif statement.type in ['elif', 'else'] and len(self.__sections) == 0:
            raise ValueError(report.error(
                "Attempted to add 'ELIF' or 'ELSE' statement without an opening 'IF' statement"
            ))
        elif statement.type in ['elif', 'else'] and self.__sections[-1].statement.type == 'else':
            raise ValueError(report.error(
                "Attempted to add section after closing 'ELSE' statement"
            ))
        # Accept the new section
        self.__sections.append(PreprocessorBlock(statement, self.__file))

    def add_line(self, line):
        """ Add a line to the last section.

        Overriding the inherited method, instead this appends the line to the last
        added section. As with inherited method this can be a string or other
        preprocessor object.

        Args:
            line: The line to add, this can be a PreprocessorLine,
                  PreprocessorBlock, or PreprocessorStatement
        """
        if len(self.__sections) == 0:
            raise PreprocessorError(report.error(
                "No section exists to append line to"
            ), path=self.__file.path)
        self.__sections[-1].add_line(line)

    def evaluate(self):
        """ Evaluate the PreprocessorIfBlock choosing the right section.

        Work through the sections, evaluating the guard statements until a 'True'
        value is returned. For the one section with a 'True' value, the contents
        of the block will be evaluated and returned.

        Returns:
            list: A list of lines from the evaluated block
        """
        result = []
        for section in self.__sections:
            if section.statement.evaluate():
                result = section.evaluate()
                break
        # NOTE: An empty result can be returned in the case we don't have an
        # 'ELSE' condition - but we shouldn't return None!
        return result
