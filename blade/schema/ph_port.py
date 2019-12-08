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
As a fairly primitive tag type, a !Port can be declared either using mapping or
sequence syntax provided you don't specify an enumeration - the same example is
shown below in both styles:

.. highlight:: yaml
.. code-block:: yaml

    - !Port [my_port, 10, "10-bit port 3 times over", 3, 0, Master, "Longer description...", [], []]

    - !Port
      name   : my_port
      width  : 10
      sd     : 10-bit port 3 times over
      count  : 3
      default: 0
      role   : Master
      ld     : Longer description...
      enum   :
      options: []

You can provide an enumeration to give names to the different values that the
port can take:

.. highlight:: yaml
.. code-block:: yaml

   - !Port
     name : state
     width: 2
     sd   : Current state of my block
     enum :
     - !Enum [off,    0]
     - !Enum [idle,   1]
     - !Enum [active, 2]
     - !Enum [failed, 3]

"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.port")

# For validation
from .ph_enum import Enum

class Port(TagBase):
    """ Defines a basic signal component with a specified width """

    yaml_tag = "!Port"

    def __init__(
        self,
        name,
        width=1,
        sd="",
        count=1,
        default=0,
        role=CONSTANTS.ROLES.MASTER,
        ld="",
        enum=None,
        options=[],
    ):
        """ Initialisation for the !Port YAML tag

        Args:
            name   : Name for the signal component
            width  : Number of bits carried by the signal
            sd     : Short description of the component - maximum 150 characters
            count  : Number of repetitions of this component
            default: The default value this component should take upon reset
            role   : Role for this port, either 'master' or 'slave'
            ld     : Long description of the port
            enum   : List of !Enum tags naming specific values the port can take
            options: List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required
        """
        super().__init__(name, sd, ld, options)
        self.width   = width
        self.count   = count
        self.default = default
        self.role    = role.strip().upper() if isinstance(role, str) else role
        self.enum    = enum if enum != None and isinstance(enum, list) else []

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'width', if non-complex, is integer and positive
        if str(self.width).strip().replace(".","").isdigit():
            if "." in str(self.width):
                raise ValidationError(
                    report.error("Port width value must be integer", item=self),
                    "width", self
                )
            elif int(self.width) <= 0:
                raise ValidationError(
                    report.error("Port width value must be >= 1", item=self),
                    "width", self
                )

        # Check that 'count', if non-complex, is integer and positive
        if str(self.count).strip().replace(".","").isdigit():
            if "." in str(self.count):
                raise ValidationError(
                    report.error("Port count value must be integer", item=self),
                    "count", self
                )
            elif int(self.count) <= 0:
                raise ValidationError(
                    report.error("Port count value must be >= 1", item=self),
                    "count", self
                )

        # Check that 'default', if non-complex, is integer
        if str(self.default).strip().replace(".","").isdigit():
            if "." in str(self.default):
                raise ValidationError(
                    report.error("Port default value must be integer", item=self),
                    "default", self
                )

        # Check that 'role' is in the list of supported options
        if not self.role in CONSTANTS.ROLES:
            raise ValidationError(
                report.error(f"Port specifies an unsupported role {self.role}", item=self),
                "role", self
            )

        # Check that 'enum' is a list only containing Enum objects
        if self.enum != None:
            if not isinstance(self.enum, list):
                raise ValidationError(
                    report.error("Port enums are not stored as a list", item=self),
                    "enum", self
                )
            bad = [x for x in self.enum if not isinstance(x, Enum)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Port enums contains {bad[0].yaml_tag}", item=self),
                    "enum", self
                )
            # Validate all enums
            for enum in self.enum:
                enum.validate()
