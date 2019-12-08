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
report = reporting.get_report("preprocessor.common")

class PreprocessorError(Exception):
    """ Custom Exception type that allows preprocessing errors to be reported """

    def __init__(self, message, path=None):
        """ Initialise the validation error.

        Args:
            message: The exception message
            path   : Path to the file being processed
        """
        super().__init__(message)
        self.path = path

# Define regular expressions used to extract different macros
preprocessor_regex = {
    'include': re.compile(r"^[ ]{0,}#(include)[ ]{0,}(.*?)$"),
    'define' : re.compile(r"^[ ]{0,}#(define)[ ]{0,}(.*?)$"),
    # IF Blocks
    'if'     : re.compile(r"^[ ]{0,}#(if|ifdef|ifndef)[\s]+(.*?)(?:# (.*?))?$"),
    'elif'   : re.compile(r"^[ ]{0,}#(elif|elseif)[\s]{0,}(.*?)$"),
    'endif'  : re.compile(r"^[ ]{0,}#(endif)[ ]{0,}"),
    'else'   : re.compile(r"^[ ]{0,}#(else)[ ]{0,}$"),
    # FOR Blocks
    'for'    : re.compile(r"^[ ]{0,}#(for)[\s]+([^\s]+[\s]+in[\s]+.*?)[\s]{0,}(?:[:])?[\s]{0,}$"),
    'endfor' : re.compile(r"^[ ]{0,}#(endfor)"),
}

def evaluate_expression(expression, file):
    """
    Evaluate an expression with access to the preprocessor scope of #define'd
    constants.

    Args:
        expression: The expression to evaluate
        file      : The PreprocessorFile instance (to get values!)
    """
    # Check this isn't already a number
    if not isinstance(expression, str):
        return expression
    elif expression.replace('.','').isdigit():
        return float(expression) if '.' in expression else int(expression)
    # Try to find and replace all constants encased in brackets '<MYCONST>'
    matches   = re.findall(r"[<]([A-Za-z]{1}[A-Za-z0-9_]+)[>]", expression)
    sanitised = expression
    for match in matches:
        value = file.resolve_value(match)
        if not value:
            raise ValueError(report.error(
                f"Could not resolve value for '{match}' in expression "
                f"'{expression}' in file: {file.path}"
            ))
        # NOTE: Only replace the first occurrence to avoid partial replacement!
        sanitised = sanitised.replace(f"<{match}>", str(value), 1)
    # Now try to find and replace any constants not enclosed in brackets 'MYCONST'
    matches = re.findall(r"[^A-Za-z0-9<]{0,1}([A-Za-z]{1}[A-Za-z0-9_]+)[^A-Za-z0-9>]{0,1}", expression)
    for match in matches:
        value = file.resolve_value(match)
        # NOTE: Only replace the first occurrence to avoid partial replacement!
        if value:
            sanitised = sanitised.replace(str(match), str(value), 1)
    # Evaluate the sanitised expression
    try:
        result = eval(sanitised)
    except:
        raise ValueError(report.error(
            f"Failed to resolve expression '{expression}' in file: {file.path}"
        ))
    return result
