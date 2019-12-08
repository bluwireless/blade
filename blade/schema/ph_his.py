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

    - !His
      name : channel
      ld   : Describes a data transmission channel with valid and acknowledgement
      ports:
      - !Port [valid,  1, "Valid signal",    1, 0, Master]
      - !Port [ack,    1, "Acknowledgement", 1, 0, Slave ]
      - !Port [data,  32, "Data carried",    1, 0, Master]

    - !His
      name : bidirectional_bus
      ld   : A bus carrying two channels with channel enable signals
      ports:
      - !HisRef [outbound, channel, "Transmit bus",   1, Master]
      - !HisRef [inbound,  channel, "Receive bus",    1, Slave ]
      - !Port   [enable,         1, "Channel enable", 2, Master]
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.his")

# For validation
from .ph_his_ref import HisRef
from .ph_port import Port

class His(TagBase):
    """ !His tag schema class for describing an interconnect with components """
    yaml_tag = "!His"

    def __init__(
        self, name, ports, sd="", role=CONSTANTS.ROLES.MASTER, ld="", options=[], includes=[]
    ):
        """ Initialisation for the !His YAML tag

        Args:
            name   : Name of the !His, used when declaring a port of this type
            ports  : List of either !HisRef or !Port tags which will be carried
                     as components within this interconnect
            sd     : Short description of the interconnect - maximum 150 characters
            role   : Declares the overall role for this interconnect, effectively
                     reversing whatever role it is declared as (to be deprecated)
            ld     : Long description of the interconnect
            options: List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required.
        """
        super().__init__(name, sd, ld, options)
        self.ports       = ports
        self.role        = role.strip().upper() if isinstance(role, str) else ""
        self.includes    = includes # TODO: Remove - not used?

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for port in self.ports:
            port.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for port in self.ports:
            if self.start_mark:
                port.shift_file_marks(start.line - self.start_mark.line)
            else:
                port.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'ports' is a list only containing Port or HisRef objects
        if self.ports != None:
            if not isinstance(self.ports, list):
                raise ValidationError(
                    report.error("His ports are not stored as a list", item=self),
                    "ports", self
                )
            bad = [x for x in self.ports if not isinstance(x, HisRef) and not isinstance(x, Port)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"His ports contains {bad[0].yaml_tag}", item=self),
                    "ports", self
                )
            # Validate all ports
            for port in self.ports:
                port.validate()

        # Check that the role is in the list of supported options
        if not self.role in CONSTANTS.ROLES:
            raise ValidationError(
                report.error(f"His specifies an unsupported role {self.role}", item=self),
                "role", self
            )
