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

    - !Mod
      name : my_distributor
      ports:
      - !HisRef [inbound_a, axi4, "Inbound from CPU", 1]
      - !HisRef [inbound_b, axi4, "Inbound from NoC", 1]
      - !HisRef [outbounds, axi4, "Outbound ports",   3]
      addressmap:
      - !Initiator
        mask: 0x1FFF
        port:
        - !Point [inbound_a, 0]
      - !Initiator
        mask     : 0x1FFF
        port     :
        - !Point [inbound_b, 0]
        constrain: # Don't allow first outbound port to be accessed
        - !Point [outbounds, 1]
        - !Point [outbounds, 2]
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.initiator")

from .ph_point import Point

class Initiator(TagBase):
    """ Represents an initiator port within the address map """
    yaml_tag = "!Initiator"

    def __init__(self, port, mask=0xFFFFFFFF, offset=0, constrain=None):
        """ Initialisation for the !Initiator tag

        Args:
            port     : !Point tag referring to the exact port and index to
                       associate
            mask     : Mask to apply to the address of incoming transactions
            offset   : Offset to apply to the address after masking
            constrain: List of !Point tags referring to legally accessible
                       !Target ports - if omitted then all targets are accessible.
        """
        super().__init__(None, None, None, None)
        self.port      = port
        self.mask      = mask
        self.offset    = offset
        self.constrain = constrain

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Check that port is a !Point instance
        if not self.port or not len(self.port) == 1 or not isinstance(self.port[0], Point):
            raise ValidationError(
                report.error("Initiator port is not declared as a !Point", item=self),
                "port", self
            )

        # Validate the port object
        self.port[0].validate()

        # Check that 'offset', if non-complex, is integer and non-negative
        if str(self.offset).strip().replace(".","").isdigit():
            if not isinstance(self.offset, int) and "." in str(self.offset):
                raise ValidationError(
                    report.error("Initiator offset value must be integer", item=self),
                    "offset", self
                )
            elif (self.offset < 0 if isinstance(self.offset, int) else int(self.offset, 0) < 0):
                raise ValidationError(
                    report.error("Initiator offset value must be >= 0", item=self),
                    "offset", self
                )

        # Check that 'mask', if non-complex, is integer and non-negative
        if str(self.mask).strip().replace(".","").isdigit():
            if not isinstance(self.mask, int) and "." in str(self.mask):
                raise ValidationError(
                    report.error("Initiator mask value must be integer", item=self),
                    "mask", self
                )
            elif (self.mask < 0 if isinstance(self.mask, int) else int(self.mask, 0) < 0):
                raise ValidationError(
                    report.error("Initiator mask value must be >= 0", item=self),
                    "mask", self
                )

        # Check that 'constrain' is a list only containing !Point objects
        if self.constrain != None:
            if not isinstance(self.constrain, list):
                raise ValidationError(
                    report.error("Initiator constraints are not stored as list", item=self),
                    "constrain", self
                )
            bad = [x for x in self.constrain if not isinstance(x, Point)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Initiator constrains contains a {bad[0].yaml_tag}", item=self),
                    "constrain", self
                )
            # Validate all constraints
            for constraint in self.constrain:
                constraint.validate()
