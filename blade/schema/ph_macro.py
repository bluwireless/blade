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
The !Macro tag is primitive, so either sequence or mapping syntax can be used
when declaring it. Examples of both are given below:

.. highlight:: yaml
.. code-block:: yaml

    - !Config
      order:
      - !Macro [inbound_ctrl, group_a, 2, 10, "Groups for inbound controls"]
      - !Macro
        name : outbound_ctrl
        macro: group_a
        array: 3
        align: 20
        ld   : Groups for outbound controls

    - !Group
      name: group_a
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.macro")

class Macro(TagBase):
    """
    Use within !Config to specify a !Group of type Macro. Has an option to
    specify a prefix, number of array and alignment.
    """
    yaml_tag = "!Macro"

    def __init__(self, name, macro, array="-", align="-", ld=""):
        """ Initialisation for the !Macro tag

        Args:
            name : Prefix to add to the name of the group for this instantiation
            macro: Name of the macro-type group being instantiated
            array: How many instances to place
            align: The word (i.e. 4-byte) alignment of the group's base address
            ld   : Long description for the macro
        """
        super().__init__(name, None, ld, None)
        self.type  = "MACRO"
        self.macro = macro
        self.array = 1 if array == "-" else array
        self.align = 1 if align == "-" else align

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: Can't validate 'macro' yet as it references a !Group

        # Check that 'array', if non-complex, is integer and positive
        if str(self.array).strip().replace(".","").isdigit():
            if "." in str(self.array):
                raise ValidationError(
                    report.error("Macro array value must be integer", item=self),
                    "array", self
                )
            elif int(self.array) <= 0:
                raise ValidationError(
                    report.error("Macro array value must be >= 1", item=self),
                    "array", self
                )

        # Check that 'align', if non-complex, is integer and positive
        if str(self.align).strip().replace(".","").isdigit():
            if "." in str(self.align):
                raise ValidationError(
                    report.error("Macro align value must be integer", item=self),
                    "align", self
                )
            elif int(self.align) <= 0:
                raise ValidationError(
                    report.error("Macro align value must be >= 1", item=self),
                    "align", self
                )
