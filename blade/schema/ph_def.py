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
As !Def is a primitive tag, either sequence or mapping syntax may be used to
declare it - examples of both are given below:

.. highlight:: yaml
.. code-block:: yaml

    - !Def [data_bus_width, 32, "Width of all data buses in the design"]
    - !Def
    name : device_id
    value: 0x12345678
    ld   : Identifier for the device
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.def")

class Def(TagBase):
    """ Declares a named valued that can be used throughout the design. """
    yaml_tag = "!Def"

    def __init__(self, name, val, sd="", ld="", options=[]):
        """ Initialisation of the !Def tag.

        Args:
            name   : Name for this value
            val    : The integer value
            sd     : Short description - maximum 150 characters
            ld     : Long description - no limit on length
            options: List of options in the form 'KEY=VAL' or just 'KEY' if a
                     value is not required.
        """
        super().__init__(name, sd, ld, options)
        self.val = val

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: No specific validation routine is required for Def as until we
        #       have all Def's in-hand we can't guarantee it will evaluate. As
        #       such the Def will be evaluated during the elaboration phase.
