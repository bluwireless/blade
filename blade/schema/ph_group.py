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

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.group")

# For validation
from .ph_reg import Reg

class Group(TagBase):
    """ Defines a group containing !Reg tags which declare the registers """
    yaml_tag = "!Group"

    ## __init__
    #  Initialisation for Group
    def __init__(
        self,
        name,
        regs,
        type=CONSTANTS.GROUP_TYPES.REGISTER,
        sd="",
        ld="",
        options="",
        array="1", # TODO: Deprecated? Remove?
    ):
        """ Initialisation for the !Group tag

        Args:
            name   : Name of the register group, will be used to refer to it
                     when instantiating it within a !Config tag.
            regs   : List of the registers declared using !Reg tags.
            type   : The type of group - either 'register' (for normal behaviour)
                     or 'macro' when this group is to be instantiated with a
                     !Macro tag.
            sd     : Short description of the block - maximum 150 characters.
            ld     : Long description of the block - no maximum length.
            options: List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required.
            array  : DEPRECATED and UNSUPPORTED, same behaviour is achievable by
                     using the !Macro tag at instantiation.
        """
        super().__init__(name, sd, ld, options)

        self.type  = (
            type.strip().upper()
            if type and len(type.strip()) > 0 else
            CONSTANTS.GROUP_TYPES.REGISTER
        )
        self.array = str(array).strip()
        self.regs  = regs

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for reg in self.regs:
            reg.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for reg in self.regs:
            if self.start_mark:
                reg.shift_file_marks(start.line - self.start_mark.line)
            else:
                reg.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'type' is supported
        if not self.type in CONSTANTS.GROUP_TYPES:
            raise ValidationError(
                report.error(f"Group specifies an unsupported type {self.type}", self=item),
                "type", self
            )

        # Check that 'regs' is a list only containing Reg objects
        if self.regs != None:
            if not isinstance(self.regs, list):
                raise ValidationError(
                    report.error("Group regs are not stored as a list", self=item),
                    "regs", self
                )
            bad = [x for x in self.regs if not isinstance(x, Reg)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Group regs contains {bad[0].yaml_tag}", self=item),
                    "regs", self
                )
            # Validate all regs
            for reg in self.regs:
                reg.validate()

        # Check that 'array', if non-complex, is integer and non-negative
        if str(self.array).strip().replace(".","").isdigit():
            if "." in str(self.array):
                raise ValidationError(
                    report.error("Group array value must be integer", self=item),
                    "array", self
                )
            elif int(self.array) < 0:
                raise ValidationError(
                    report.error("Group array value must be >= 0", self=item),
                    "array", self
                )
