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
The !Const tag is primitive, so it is preferable to use sequence rather than
mapping syntax - although both are allowed:

.. highlight:: yaml
.. code-block:: yaml

    - !Connect
      const:
      - !Point [a_port, child_block]
      - !Const [1]

    - !Connect
      const:
      - !Point [b_port, child_block]
      - !Const
        value: 2
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.const")

class Const(TagBase):
    """ Defines a constant value tie for a port """
    yaml_tag = "!Const"

    def __init__(self, value, name="unknown"):
        """ Initialisation of the !Const tag

        Args:
            value: The value to tie the port to
            name : Optional name for the value
        """
        super().__init__(name, None, None, None)
        self.value = str(value)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'value', if non-complex, is integer
        if str(self.value).strip().replace(".","").isdigit():
            if "." in str(self.value):
                raise ValidationError(
                    report.error("Const value must be integer", item=self),
                    "value", self
                )
