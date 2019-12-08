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
      name: my_reg_group
      regs:
      - !Reg
      ...

    - !Group
      name: my_macro
      type: MACRO
      regs:
      - !Reg
      ...

    - !Config
      order:
      - !Register [my_reg_group]
      - !Macro    [inst_1, my_macro, 4, 100, "Array of 4 macros, each aligned to a 100 word boundary"]
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.config")

# For validation
from .ph_group import Group
from .ph_register import Register
from .ph_macro import Macro

class Config(TagBase):
    """
    A !Config allows for an optional selective order of which groups are to be
    processed. This allows a Macro-type group to be mixed with a Register-type
    group.
    """
    yaml_tag = "!Config"

    def __init__(self, order=[], name=None, options=[]):
        """ Initialisation for the !Config YAML tag

        Args:
            order  : List of !Register and !Macro tags to specify the order that
                     register groups should be instantiated
            name   : Name of the configuration (not currently used)
            options: List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required
        """
        super().__init__(name, None, None, options)
        self.order = order

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'order' is a list only containing Group objects
        if self.order != None:
            if not isinstance(self.order, list):
                raise ValidationError(
                    report.error("Config order is not stored as a list", item=self),
                    "order", self
                )
            bad = [x for x in self.order if not type(x) in [Group, Register, Macro]]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Config order contains {bad[0].yaml_tag}", item=self),
                    "order", self
                )
            # Validate all order
            for group in self.order:
                group.validate()
