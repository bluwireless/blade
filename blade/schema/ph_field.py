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
The !Field tag is relatively primative, so can be used with either sequence or
mapping syntax - although the value cannot be enumerated when using sequence
syntax. Examples of both forms are given below.

.. highlight:: yaml
.. code-block:: yaml

    - !Reg
      name  : status
      width : 32
      fields:
      - !Field [uptime, 24, 0, U, 0, "How many seconds system has been up"]
      - !Field
        name : state
        width: 1
        lsb  : 24
        sd   : Current system state
        reset: 0
        enums:
        - !Enum [inactive, 0, "System has not been configured"]
        - !Enum [active,   1, "System is ready to receive data"]
      - !Field
        name : mode
        width: 4
        msb  : 31
        sd   : Mode of operation
        reset: 0
        enums:
        - !Enum [idle,     0, "Waiting for next instruction"]
        - !Enum [transmit, 1, "Currently transmitting data"]
        - !Enum [receive,  2, "Currently receiving data"]
        ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.field")

# For validation
from .ph_enum import Enum

class Field(TagBase):
    """
    Defines a field within a register with name, width, type, and optional
    enumeration of the value.
    """
    yaml_tag = "!Field"

    def __init__(
        self,
        name,
        width="-",
        lsb=None,
        type="-",
        reset="-",
        ld="",
        sd="",
        msb=None,
        enums=None,
        options=None,
        enum=None,
    ):
        """ Initialisation for the !Field tag

        Args:
            name    : The name of the field
            width   : How many bits wide it should be
            lsb     : Least significant bit, controls placement within the register
            type    : Whether the field holds a signed or unsigned value
            reset   : The value that should be taken at reset
            ld      : Long description of the field - no maximum length
            sd      : Short description of the field - maximum 150 characters
            msb     : Most significant bit, alternative placement within the register
            enums   : List of enumerated values using !Enum tags
            options : List of optiosn either in the form 'KEY=VALUE' or just 'KEY'
                      if a value is not required.
            enum    : Alternative to 'enums'
        """
        super().__init__(name, sd, ld, options)
        self.enums    = enums if isinstance(enums, list) else (enum if isinstance(enum, list) else [])
        self.width    = 1 if "-" == width else width
        self.lsb      = None if "-" == lsb else lsb
        self.type     = "U" if "-" == type else type.strip().upper()
        self.reset    = 0 if "-" == reset else reset
        self.msb      = None if "-" == msb else msb

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for enum in (self.enums if self.enums else []):
            enum.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for enum in (self.enums if self.enums else []):
            if self.start_mark:
                enum.shift_file_marks(start.line - self.start_mark.line)
            else:
                enum.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'enums' is a list only containing Enum objects
        if self.enums != None:
            if not isinstance(self.enums, list):
                raise ValidationError(
                    report.error("Field enums are not stored as a list", item=self),
                    "enums", self
                )
            bad = [x for x in self.enums if not isinstance(x, Enum)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Field enums contains {bad[0].yaml_tag}", item=self),
                    "enums", self
                )
            # Validate all enums
            for enum in self.enums:
                enum.validate()

        # Check that 'width', if non-complex, is integer and positive
        if self.width and str(self.width).strip().replace(".","").isdigit():
            if "." in str(self.width):
                raise ValidationError(
                    report.error("Field width value must be integer", item=self),
                    "width", self
                )
            elif int(self.width) <= 0:
                raise ValidationError(
                    report.error("Field width value must be >= 1", item=self),
                    "width", self
                )
        elif not self.width or str(self.width.strip()) == 0:
            raise ValidationError(
                report.error(f"Field width has not been defined", item=self),
                "width", self
            )

        # Check that 'lsb', if non-complex, is integer and non-negative
        if str(self.lsb).strip().replace(".","").isdigit():
            if "." in str(self.lsb):
                raise ValidationError(
                    report.error("Field lsb value must be integer", item=self),
                    "lsb", self
                )
            elif int(self.lsb) < 0:
                raise ValidationError(
                    report.error("Field lsb value must be >= 0", item=self),
                    "lsb", self
                )

        # Check that the type is in the list of supported options
        if not self.type in CONSTANTS.FIELD_TYPES:
            raise ValidationError(
                report.error(f"Field specifies an unsupported type {self.type}", item=self),
                "type", self
            )

        # Check that 'reset', if non-complex, is integer
        if str(self.reset).strip().replace(".","").isdigit():
            if "." in str(self.reset):
                raise ValidationError(
                    report.error("Field reset value must be integer", item=self),
                    "reset", self
                )

        # Check that 'msb', if non-complex, is integer and non-negative
        if str(self.msb).strip().replace(".","").isdigit():
            if "." in str(self.msb):
                raise ValidationError(
                    report.error("Field msb value must be integer", item=self),
                    "msb", self
                )
            elif int(self.msb) < 0:
                raise ValidationError(
                    report.error("Field msb value must be >= 0", item=self),
                    "msb", self
                )

        # NOTE: Unsure how to validate 'opp' or 'hir_name' as usage unclear
