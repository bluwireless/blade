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
The !Enum tag is primitive and so it may be declared using either sequence or
mapping syntax - examples of both formats are given below:

.. highlight:: yaml
.. code-block:: yaml

    - !Field
      name : my_field
      width: 2
      enums:
      - !Enum [state_a, 0, "First state"]
      - !Enum
        name: state_b
        val : 1
        sd  : Second state
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.enum")

class Enum(TagBase):
    """ Enumerates the value of a !Field or !Port using named constants """
    yaml_tag = "!Enum"

    def __init__(self, name, val="", sd="", ld="", options=[], hir_name=""):
        """ Initialisation of the !Enum tag

        Args:
            name    : Name of the discretised value
            val     : The integer value this enumerated item should represent
            sd      : Short description of the value - maximum 150 characters
            ld      : Long description - no maximum length
            options : List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required.
            hir_name: Deprecated - to be removed.
        """
        super().__init__(name, sd, ld, options)
        self.val        = val
        self.hir_name   = hir_name # TODO: Deprecated - remove?

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'val', if non-complex, is an integer
        if str(self.val).strip().replace(".","").isdigit():
            if "." in str(self.val):
                raise ValidationError(
                    report.error("Enum val value must be integer", item=self),
                    "val", self
                )
