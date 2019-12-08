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

import yaml
from yaml.error import Mark
import inspect
from .schema_helpers import convert_to_class

from .. import reporting
report = reporting.get_report("schema.tag_base")

# Constants required to parse YAML
CONSTANTS = convert_to_class({
    'MAX_SD_LINE_LENGTH': 150,
    'ROLES': {
        'MASTER' : 'MASTER',
        'SLAVE'  : 'SLAVE',
        'BI'     : 'BI',
        'UNKNOWN': 'UNKNOWN',
    },
    'GROUP_TYPES': { # For !Group.type
        'REGISTER': 'REGISTER',
        'MACRO'   : 'MACRO',
    },
    'FIELD_TYPES': { # For !Field.type
        'U'      : 'U',
        'S'      : 'S',
        'CMD_DEF': 'CMD_DEF',   # TODO: Used by MAC_CMD_DEFINES, should create a dedicated !Command tag
    },
    'ACCESS': { # For !Reg.busaccess, .blockaccess, .instaccess
        'NONE':   '',   # No access
        'RW'  : 'RW',
        'WO'  : 'WO',
        'WS'  : 'WS',
        'WC'  : 'WC',
        'RO'  : 'RO',
        'AW'  : 'AW',    # Active Write: Write value qualified by strobe
        'AR'  : 'AR',    # Active Read : Strobe signal high on read
        'ARW' : 'ARW',   # Active Read/Write: Both strobes present
    },
    'ACCESS_ALIASES': { # For !Reg - mapping 'WR' -> 'RW' etc.
        'WR': 'RW',
        'R' : 'RO',
        'W' : 'WO',
    },
    'USAGE': {  # For !Reg.usage
        'START_OF_DAY'  : 'start-of-day',
        'QUIESCENT_ONLY': 'quiescent-only',
        'DYNAMIC'       : 'dynamic',
        'DEBUG_ONLY'    : 'debug-only',
        'REQUIRED'      : 'required',
        'DO_NOT_VERIFY' : 'do-not-verify',
    },
    'LOCATION': { # For !Reg.location
        'CORE'    : 'core',     # Accesses handled by implementation
        'INTERNAL': 'internal', # Generated interface handles reads and writes
        'WRAPPER' : 'wrapper',  # ?
    },
    'OPTIONS': {
        # ======================================================================
        # Options for !Mod
        # ======================================================================
        'NO_AUTO_CLK_RST'   : 'no_auto_clk_rst',    # Don't create implicit clock and reset signals
        'NO_CLK_RST'        : 'no_clk_rst',         # Block has no clock and reset signals
        # Automatic register decode signal bundling (properties propagate downwards)
        'DECODE_ON'         : 'decode_on',          # Enable bundling for a !Config, !Group, or !Reg
        'DECODE_OFF'        : 'decode_off',         # Disable bundling for a !Config, !Group, or !Reg
        'DECODE_CONTROL'    : 'decode_control',     # Enable control signals for a !Config, !Group, or !Reg (e.g. block value reset)
        'DECODE_CONTROL_OFF': 'decode_control_off', # Disable control signals for a !Config, !Group, or !Reg
        'DECODE_RETIME'     : 'decode_retime',      # Indicates the !Config should use a retiming stage on the inbound port
        # ======================================================================
        # Options for !Port
        # ======================================================================
        'AUTO_CLK'          : 'auto_clk',           # Signifies this port as the automatic clock signal
        'AUTO_RST'          : 'auto_rst',           # Signifies this port as the automatic reset signal
        # ======================================================================
        # Options for !Group
        # ======================================================================
        'BYTE'              : 'byte',               # Enable byte addressing mode
        # ======================================================================
        # Options for !Reg
        # ======================================================================
        'EVENT'             : 'event',              # Expand !Reg as an interrupt register
        'HAS_MODE'          : 'has_mode',           # Allows configuration of either LEVEL or EDGE sensitivity
        'HAS_LEVEL'         : 'has_level',          # Allows configuration of the type of LEVEL or EDGE sensitivity (high/low, or rising/falling)
        'NO_LEVEL'          : 'no_level',           # Explicitly don't provide control of LEVEL or EDGE sensitivity
        'SETCLEAR'          : 'setclear',           # Expand !Reg as a set-clear-value trio
    },
})

class ValidationError(Exception):
    """ Custom Exception type that allows validation errors to be reported """

    def __init__(self, message, parameter, doc):
        """ Initialise the validation error.

        Args:
            message  : The exception message
            parameter: The parameter that failed validation
            doc      : The document being validated
        """
        super().__init__(message)
        self.parameter = parameter
        self.doc       = doc

class TagBase(yaml.YAMLObject):
    """
    Holds name, short and long descriptions and options. Base class for all YAML
    Tags has name, options, sd and ld.  Also tracks source node for better error
    reporting.
    """

    def __init__(self, name, sd, ld, options, start=None, end=None, source=None):
        """ Initialisation for TagBase

        Args:
            name   : Name of the node
            sd     : Short description - no longer that 150 characters
            ld     : Long description - no limit on length
            options: List of options of the form 'KEY=VAL' or just 'KEY' if no
                     value is required
            start  : Tag start mark from YAML parser
            end    : Tag end mark from YAML parser
            source : Path to the source file that contained this tag
        """
        # Trim any leading or trailing whitespace from inbound variables
        self.name = name.strip().replace(" ", "_") if isinstance(name, str) else ""
        self.sd   = sd.strip() if isinstance(sd, str) else ("" if sd == None else sd)
        self.ld   = ld.strip() if isinstance(ld, str) else ("" if ld == None else ld)

        # Detect camal case in the name and convert to '_' separation
        if len(self.name) > 0 and not self.name.islower() and not self.name.isupper():
            sanitised = self.name[0].replace(" ","_")
            for char in self.name[1:]:
                if char.isupper() and sanitised[-1].islower():
                    sanitised += "_"
                sanitised += char.lower()

        # If no short description was provided, trim down the long description
        if len(self.sd) == 0 and len(self.ld) > 0:
            self.sd = self.ld.replace("\n", " ")[:CONSTANTS.MAX_SD_LINE_LENGTH]
            # Trim back to the last sentence termination if possible
            if self.sd.rfind(".") > 0:
                self.sd = self.sd[:self.sd.rfind(".")+1]

        # If no long description was provided, copy the short description
        self.ld = self.ld if len(self.ld) > 0 else self.sd

        # Ensure the options list is always an array, unless we don't recognise
        # the type of the incoming data
        if isinstance(options, str):
            if "," in options: # Support for options separated by commas
                self.options = [x.strip() for x in options.split(',')]
            else: # Support for options separated by spaces (Ifor's style)
                self.options = [x for x in options.strip().split(' ') if len(x) > 0]
        elif isinstance(options, list):
            self.options = options
        elif options == None:
            self.options = []
        else:
            self.options = None

        # Initialise the start_mark and end_mark - these demarcate the lines
        # where this tag was declared
        self.__start_mark = start
        self.__end_mark   = end

        # Initialise the source file - allows exception unwinding to print lines
        self.__source = source

        # Store documents that this one has been converted into, for example this
        # is used where a !Group is converted to a signal bundle, the resulting
        # !His is attached as a converted document.
        self.__conversions = []

    @property
    def start_mark(self):
        return self.__start_mark

    @property
    def end_mark(self):
        return self.__end_mark

    @property
    def source(self):
        return self.__source

    @property
    def conversions(self):
        return self.__conversions

    def set_file_marks(self, start, end):
        """ Set the start and end marks of this tag's declaration

        Args:
            start: The starting mark of the declaration
            end  : The ending mark
        """
        self.__start_mark = start
        self.__end_mark   = end

    def shift_file_marks(self, line_offset, column_offset=0):
        """ Shift the stored file marks by an offset value.

        Args:
            line_offset  : The number of lines the file mark has moved by
            column_offset: The number of columns the file mark has moved by
        """
        self.__start_mark = Mark(
            self.__start_mark.name, self.__start_mark.index,
            self.__start_mark.line + line_offset,
            self.__start_mark.column + column_offset,
            self.__start_mark.buffer, self.__start_mark.pointer
        )
        self.__end_mark = Mark(
            self.__end_mark.name, self.__end_mark.index,
            self.__end_mark.line + line_offset,
            self.__end_mark.column + column_offset,
            self.__end_mark.buffer, self.__end_mark.pointer
        )

    def set_source_file(self, file):
        """
        Set the source file that this tag was generated from (this can be a string
        or object - in the case of a preprocessor)

        Args:
            file: The path or object representing the source file
        """
        if self.__source:
            raise Exception(report.error(
                "Source file has already been set for this tag", item=self
            ))
        self.__source = file

    def add_conversion(self, doc):
        """ Add a new document that this tag instance has been converted into.

        Args:
            doc: The resulting document from the conversion
        """
        self.__conversions.append(doc)

    def validate(self):
        """ Check that variables are acceptable within the YAML schema """
        # Check that the short description is acceptable
        if not isinstance(self.sd, str):
            raise ValidationError(
                report.error(f"Short description is not of string type", item=self),
                "sd", self
            )
        elif len(self.sd) > CONSTANTS.MAX_SD_LINE_LENGTH:
            raise ValidationError(
                report.error(f"Short description is too long ({len(self.sd)}, {CONSTANTS.MAX_SD_LINE_LENGTH})", item=self),
                "sd", self
            )
        elif len(self.sd.splitlines()) > 1:
            raise ValidationError(
                report.error(f"Short description spans over multiple {len(self.sd.splitlines())} lines", item=self),
                "sd", self
            )

        # Check that the long description is acceptable
        if not isinstance(self.ld, str):
            raise ValidationError(
                report.error(f"Long description is not of string type", item=self),
                "ld", self
            )

        # Check that the options list is an array
        if not isinstance(self.options, list):
            raise ValidationError(
                report.error(f"Options list is not of a recognised type", item=self),
                "options", self
            )

    def print_source(self):
        """
        Return the source definition file info as a string - we have to trace
        this back through the preprocessor.
        """
        if self.__source != None:
            input_line = None
            try:
                input_line = self.__source.get_input_line_number(self.__start_mark.line)
            except ValueError:
                input_line = "UNKNOWN"
            return f"defined in {self.__source.path} on line {input_line}"
        else:
            return "UNKNOWN"

    def get_source_file_name(self):
        """ Return the source file as a string. """
        return self.__source.file if self.__source else None

    def get_repo_name(self):
        """
        Return the name of the repository that contained the source file, note
        that we rely on the name of the scope held by the preprocessor.
        """
        return self.__source.scope if self.__source else None

    def get_repo_rev(self):
        """
        [DEPRECATED] This is unnecessary once you have the path, so it's been
        deprecated as the method of finding the revision is sensitive to the
        folder structure.
        """
        raise Exception(report.error(
            "get_repo_rev is deprecated due to being unnecessary", item=self
        ))

    def __repr__(self):
        """
        Generate an automatic representation of this block when it is converted
        to a string.
        """
        members = [
            x for x in inspect.getmembers(self)
            if not '__' in x[0] and type(x[1]) in [list, map, str, int, float, bool]
        ]
        out = [f"{type(self).__name__} => " + "{"]
        for item in members:
            if type(item[1]) in [str, int, float, bool]:
                out.append(f"  {item[0]}: {item[1]}")
            elif isinstance(item[1], list) and len(item[1]) > 0:
                out.append(f"  {item[0]}: [")
                for entry in item[1]:
                    out.append("    "+"    ".join(entry.__repr__().splitlines(True)))
                out.append("  ]")
            elif isinstance(item[1], map) and len(item[1].keys()) > 0:
                out.append(f"  {item[0]}: " + "{")
                for key in item[1]:
                    out.append(f"    {key}:")
                    out.append("      "+"      ".join(entry.__repr__().splitlines(True)))
                out.append("  }")
        out.append("}")
        return "\n".join(out)
