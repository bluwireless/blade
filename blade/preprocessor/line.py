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
report = reporting.get_report("preprocessor.line")

from .common import PreprocessorError

class PreprocessorLine(str):
    """
    Extends from 'str' to provide a custom string class that can track the input
    and output line numbers to allow us to relate parse errors back to original
    lines of source code.
    """

    @property
    def source_file(self):
        """ Return the PreprocessorFile that contains this line """
        return self.__source_file if hasattr(self, "_PreprocessorLine__source_file") else None

    @source_file.setter
    def source_file(self, value):
        """ Set the PreprocessorFile that contains this line, if not yet set """
        if hasattr(self, "_PreprocessorLine__source_file"):
            raise PreprocessorError(report.error(
                "A source file has already been set for this line"
            ), path=self.__source_file.path)
        self.__source_file = value

    @property
    def input_line(self):
        """ Get the line number in the input file this line came from """
        return self.__input_line if hasattr(self, "_PreprocessorLine__input_line") else -1

    @input_line.setter
    def input_line(self, value):
        """ Set the line number in the input file this line came from """
        if hasattr(self, "_PreprocessorLine__input_line"):
            raise PreprocessorError(report.error(
                f"A line number ({self.__input_line}) has already been set for this line"
            ), path=self.__source_file.path)
        self.__input_line = value

    @property
    def output_line(self):
        """ Get the line number within the output file that this line appears at """
        return self.__output_line if hasattr(self, "_PreprocessorLine__output_line") else -1

    @output_line.setter
    def output_line(self, value):
        """ Set the line number in the output file that this line appears at """
        if hasattr(self, "_PreprocessorLine__output_line"):
            raise PreprocessorError(report.error(
                f"A line number ({self.__output_line}) has already been set for this line"
            ), path=self.__source_file.path)
        self.__output_line = value

    def strip(self):
        """ Override the normal strip method to return another PreprocessorLine object """
        result = PreprocessorLine(super().strip())
        result.source_file = self.__source_file if hasattr(self, "_PreprocessorLine__source_file") else None
        result.input_line  = self.__input_line if hasattr(self, "_PreprocessorLine__input_line") else -1
        result.output_line = self.__output_line if hasattr(self, "_PreprocessorLine__output_line") else -1
        return result
