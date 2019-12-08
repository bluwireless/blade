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

from .block import PreprocessorBlock
from .line import PreprocessorLine
from .common import evaluate_expression

from .. import reporting
report = reporting.get_report("preprocessor.for_block")

# Create regular expression to recognise use of iterator variable
rgx_iter = re.compile(r"\$\((.*?)\)")

class PreprocessorForBlock(PreprocessorBlock):
    """
    Represents a block that should be repeatedly evaluated based on the iterable
    defined in the statement. This block doesn't directly contain lines, but
    instead holds the loop's contents in an instance of PreprocessorBlock.
    """

    def __init__(self, statement, file):
        """ Initialisation function for a preprocessor block.

        Note that lines are not initially included, as they are appended to the
        block once it's created.

        Args:
            statement: The PreprocessorStatement that controls this block
            file     : Reference to the PreprocessorFile for resolving values.
        """
        super().__init__(statement, file)
        self.__block = PreprocessorBlock(statement, file)

    def add_line(self, line):
        """ Add line to the block.

        Overriding the inherited method, instead this appends the line to the
        encased PreprocessorBlock that represents the loop's contents.

        Args:
            line: The PreprocessorLine, PreprocessorStatement, or PreprocessorBlock
                  instance to add to the block.
        """
        self.__block.add_line(line)

    def evaluate(self):
        """ Evaluate the PreprocessorForBlock replacing uses of the iteration variable.

        Evaluate the opening statement to determine how many times the loop should
        be repeated. The generate a result, replacing any usage of the iteration
        variable on each pass.

        Returns:
            list: A list of lines from the evaluated block
        """
        inner   = self.__block.evaluate()
        control = self.__block.statement.evaluate()
        result  = []
        for i in control['iterable']:
            for line in inner:
                sanitised = line
                # Replace all uses of the iteration variable with evaluated expressions
                rgx_index = re.compile(r"(^|[^\w])" + control['variable'] + r"($|[^\w])")
                uses      = (x for x in rgx_iter.findall(line) if control['variable'] in x)
                # if 'beam' in control['variable'] or 'suffix' in control['variable']:
                #     import pdb; pdb.set_trace()
                for use in uses:
                    # First check that the correct control variable is used here
                    if not rgx_index.match(control['variable']):
                        continue
                    # First work out what the replacement text is going to be
                    if not isinstance(i, str) or i.replace('.','').strip().isdigit():
                        replacement = rgx_index.sub(r"\g<1>" + str(i) + r"\g<2>", use)
                    else:
                        replacement = rgx_index.sub(r'\g<1>"' + str(i) + r'"\g<2>', use)
                    if replacement == None:
                        continue
                    # Attempt to resolve the replacement
                    try:
                        replacement = str(eval(replacement))
                    except Exception:
                        pass
                    # Perform the replacement
                    sanitised = sanitised.replace(f"$({use})", replacement)
                # Keep track of the line in the source file
                new_line = PreprocessorLine(sanitised)
                new_line.source_file = line.source_file
                new_line.input_line  = line.input_line
                result.append(new_line)
        return result
