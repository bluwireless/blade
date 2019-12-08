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
.. highlight:: yaml
.. code-block:: yaml

    - !Group
      name: my_grp
      ...
      regs:
      - !Reg
        name       : channel_status
        addr       : 4
        array      : 2
        blockaccess: RW
        busaccess  : RO
        fields     :
        - !Field [bypass, 1, 0, U, 0, "Bypass mode active"]
        - !Field
          name : state
          sd   : "Read back a channel's current status"
          width: 2
          enums:
          - !Enum [disabled, 0, "Not yet been enabled"]
          - !Enum [idle,     1, "Enabled but not busy"]
          - !Enum [busy,     2, "Enabled and actively consuming data"]
          - !Enum [error,    3, "Hit an error case, waiting to be reset"]
    - !Reg
      name       : control
      align      : 8
      blockaccess: AW
      fields     :
      - !Field
        name : start
        width: 2
        sd   : Activate a channel by writing its ID
      - !Field
        name : stop
        width: 2
        sd   : Stop a channel by writing its ID
    - !Reg
      name   : my_interrupt_input
      options: [EVENT, HAS_LEVEL, HAS_MODE]
      fields :
      ...
    - !Reg
      name   : my_setclear
      options: [SETCLEAR]
      fields :
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.reg")

# For validation
from .ph_field import Field

class Reg(TagBase):
    """
    Defines a register containing a list of fields. The register can have
    different access types, and can be positioned at a specific address or
    aligned to the next convenient boundary.
    """
    yaml_tag = "!Reg"

    def __init__(
        self,
        name="",
        addr="",
        array=1,
        align=1,
        blockaccess=CONSTANTS.ACCESS.RW,
        busaccess=CONSTANTS.ACCESS.RW,
        instaccess=CONSTANTS.ACCESS.RW,
        options="",
        sd="",
        ld="",
        location="",
        protect="", # TODO: Deprecated - remove?
        parent="",  # TODO: Deprecated - remove?
        width=32,
        max_bit=0,  # TODO: Deprecated - remove?
        fields=[],
        usage=CONSTANTS.USAGE.REQUIRED, # TODO: Deprecated - remove?
    ):
        """ Initialisation for the !Reg tag.

        Args:
            name       : Name of the register
            addr       : Address to place the register, if omitted then the
                         elaborator will place this at the next available address
                         in accordance with its 'align' requirement.
            array      : Number of instances of the register to place consecutively
            align      : The alignment requirement of the first register, if
                         'array' is set > 1 then each instantiation will be placed
                         at a consecutive address - the alignment constraint is
                         not applied.
            blockaccess: Whether the block holding this register can access or
                         modify the value.
            busaccess  : Whether initiators on the bus can access or modify the
                         value of the register, and whether read or write strobe
                         signals are required.
            instaccess : Whether instructions executing within this block can
                         access or modify the value of the register, suitable for
                         use in CPU style register banks.
            options    : List of options either in the form 'KEY=VALUE' or just
                         'KEY' if a value is not required.
            sd         : Short description of the register - maximum 150 characters
            ld         : Long description of the register - no maximum length
            location   : Describes at what level the register is implemented,
                         either `internal`, `wrapper`, or `core`.
            protect    : Deprecated attribute, will be removed.
            parent     : Deprecated attribute, will be removed.
            width      : Set the width of the register - defaults to 32-bits.
            max_bit    : Deprecated attribute, will be removed.
            fields     : A list of !Field tags declaring the fields of the register.
            usage      : Deprecated attribute, will be removed.
        """
        super().__init__(name, sd, ld, options)
        self.addr        = addr
        self.array       = array
        self.align       = align
        if blockaccess == " ":
            self.blockaccess = CONSTANTS.ACCESS.NONE
        elif blockaccess in ["", "-"]:
            self.blockaccess = CONSTANTS.ACCESS.RW
        else:
            self.blockaccess = blockaccess.strip().upper()
        self.busaccess   = CONSTANTS.ACCESS.RW   if busaccess   in ["", "-"] else busaccess.strip().upper()
        self.instaccess  = CONSTANTS.ACCESS.NONE if instaccess  in ["", "-"] else instaccess.strip().upper()
        self.location    = location.strip()
        self.protect     = protect
        self.parent      = parent
        self.width       = width
        self.max_bit     = max_bit
        self.fields      = fields
        self.usage       = [
            x.lower().strip() for x in ([usage] if isinstance(usage, str) else usage)
        ]

        # Check if access have alias values
        aliases = CONSTANTS.ACCESS_ALIASES
        self.blockaccess = aliases[self.blockaccess] if self.blockaccess in aliases else self.blockaccess
        self.busaccess   = aliases[self.busaccess]   if self.busaccess   in aliases else self.busaccess
        self.instaccess  = aliases[self.instaccess]  if self.instaccess  in aliases else self.instaccess

        # If no location is force, derive if from roles
        if len(self.location) == 0:
            if self.busaccess in [
                CONSTANTS.ACCESS.RW, CONSTANTS.ACCESS.WO
            ]:
                self.location = CONSTANTS.LOCATION.INTERNAL
            elif self.busaccess in [CONSTANTS.ACCESS.WS, CONSTANTS.ACCESS.WC]:
                self.location = CONSTANTS.LOCATION.WRAPPER
            elif self.busaccess in [
                CONSTANTS.ACCESS.RO, CONSTANTS.ACCESS.AW,
                CONSTANTS.ACCESS.AR, CONSTANTS.ACCESS.ARW
            ]:
                self.location = CONSTANTS.LOCATION.CORE

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for field in self.fields:
            field.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for field in self.fields:
            if self.start_mark:
                field.shift_file_marks(start.line - self.start_mark.line)
            else:
                field.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'array', if non-complex, is integer and positive
        if str(self.array).strip().replace(".","").isdigit():
            if "." in str(self.array):
                raise ValidationError(
                    report.error("Reg array value must be integer", item=self),
                    "array", self
                )
            elif int(self.array) <= 0:
                raise ValidationError(
                    report.error("Reg array value must be >= 1", item=self),
                    "array", self
                )

        # Check that 'align', if non-complex, is integer and positive
        if str(self.align).strip().replace(".","").isdigit():
            if "." in str(self.align):
                raise ValidationError(
                    report.error("Reg align value must be integer", item=self),
                    "align", self
                )
            elif int(self.align) <= 0:
                raise ValidationError(
                    report.error("Reg align value must be >= 1", item=self),
                    "align", self
                )

        # Check that 'addr', if non-complex, is integer and non-negative
        if str(self.addr).strip().replace(".","").isdigit():
            if "." in str(self.addr):
                raise ValidationError(
                    report.error("Reg addr value must be integer", item=self),
                    "addr", self
                )
            elif int(self.addr) < 0:
                raise ValidationError(
                    report.error("Reg addr value must be >= 0", item=self),
                    "addr", self
                )

        # Check that the blockaccess is in the list of supported options
        if not self.blockaccess in [
            CONSTANTS.ACCESS.RO, CONSTANTS.ACCESS.WO, CONSTANTS.ACCESS.RW,
            CONSTANTS.ACCESS.NONE,
        ]:
            raise ValidationError(
                report.error(f"Reg specifies an unsupported blockaccess \"{self.blockaccess}\"", item=self),
                "blockaccess", self
            )

        # Check that the instaccess is in the list of supported options
        if not self.instaccess in [
            CONSTANTS.ACCESS.RO, CONSTANTS.ACCESS.WO, CONSTANTS.ACCESS.RW,
            CONSTANTS.ACCESS.NONE,
        ]:
            raise ValidationError(
                report.error(f"Reg specifies an unsupported instaccess \"{self.instaccess}\"", item=self),
                "instaccess", self
            )

        # Check that the busaccess is in the list of supported options
        if not self.busaccess in CONSTANTS.ACCESS.values():
            raise ValidationError(
                report.error(f"Reg specifies an unsupported busaccess \"{self.busaccess}\"", item=self),
                "busaccess", self
            )

        # Check that location is in the list of supported options
        if not self.location in CONSTANTS.LOCATION.values():
            raise ValidationError(
                report.error(f"Reg specifies an unsupported location \"{self.location}\"", item=self),
                "location", self
            )

        # Check that 'width', if non-complex, is integer and positive
        if str(self.width).strip().replace(".","").isdigit():
            if "." in str(self.width):
                raise ValidationError(
                    report.error("Reg width value must be integer", item=self),
                    "width", self
                )
            elif int(self.width) <= 0:
                raise ValidationError(
                    report.error("Reg width value must be >= 1", item=self),
                    "width", self
                )

        # Check that 'fields' is a list only containing Field objects
        if self.fields != None:
            if not isinstance(self.fields, list):
                raise ValidationError(
                    report.error("Reg fields are not stored as a list", item=self),
                    "fields", self
                )
            bad = [x for x in self.fields if not isinstance(x, Field)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Reg fields contains {bad[0].yaml_tag}", item=self),
                    "fields", self
                )
            # Validate all fields
            for field in self.fields:
                field.validate()
