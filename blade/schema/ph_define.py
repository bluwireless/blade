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

    - !Define
      group: my_reg_group
      name : my_reg
      field: my_field
      reset: 4
      width: 6
      enum :
      - !Enum [first, 0]
      ...

    - !Define
      group      : my_reg_group
      name       : my_reg
      busaccess  : RO
      blockaccess: ARW
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.define")

class Define(TagBase):
    """ Overrides specific parameters of a defined register """
    yaml_tag = "!Define"

    def __init__(
        self,
        name="",
        group="",
        reg="",
        field="",
        enum="",
        array="",
        align="",
        width="",
        reset="",
        blockaccess="",
        busaccess="",
        instaccess="",
    ):
        """ Initialisation for the !Define tag.

        Args:
            name       : Name of the override
            group      : Group of the register to override
            reg        : Name of the register to override
            field      : Which field is being modified (only required for
                         changing attributes of a field, omit if modifying the
                         register)
            enum       : New enumeration values to replace those in the base
                         description of the !Field
            array      : Modify the number of instances of a specific register
            align      : Modify the alignment parameter for the register
            width      : Modify the width of the register
            reset      : Modify the reset value of the register
            blockaccess: Modify the block access privileges
            busaccess  : Modify the bus access privileges
            instaccess : Modify the instruction access privileges
        """
        super().__init__(name if name else group, None, None, None)
        self.group       = group
        self.reg         = reg
        self.field       = field
        self.enum        = enum
        self.array       = array
        self.align       = align
        self.width       = width
        self.reset       = reset
        self.blockaccess = blockaccess
        self.busaccess   = busaccess
        self.instaccess  = instaccess

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: Unsure of what validation needs to be performed as unclear
        #       unclear if this tag is still in use?
