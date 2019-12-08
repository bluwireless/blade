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
The !Point tag can be used in two different contexts, an example of each is given
below. The tag is primitive, so either mapping or sequence syntax can be used:

.. highlight:: yaml
.. code-block:: yaml

    - Mod
      name : my_mod
      ports:
      - !HisRef [initiators, axi4, "Initiators onto the NoC", 4, Slave]
      - !HisRef [targets,    axi4, "Targets from the NoC",    4, Master]
      modinst:
      - !ModInst [block_a, type_1, "First block",  1]
      - !ModInst [block_b, type_1, "Second block", 1]
      - !ModInst [block_c, type_1, "Third block",  1]
      - !ModInst [block_d, type_1, "Fourth block", 1]
      connections:
      - !Connect
        connect:
        - !Point [initiators]
        - !Point [init, block_a]
        - !Point [init, block_b]
        - !Point [init, block_c]
        - !Point
          name: init
          mod : block_d
      ...
      defaults:
      - !Point [unused_out, block_a] # Tie-off an unused signal to supress errors
      addressmap:
      - !Initiator
        mask: 0x1FFF
        port:
        - !Point [initiators, 0]
      ...
      - !Target
        offset  : 0x0800
        aperture: 0x1000
        port    :
        - !Point [targets, 2] # NOTE: Second field here selects a single port within 'targets'
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.point")

class Point(TagBase):
    """
    Reference to a port on a particular module, if no module name is provided
    then it is taken to be a port on the module in the current scope. Also used
    to identify a specific index of a port where count has been set > 1.
    """
    yaml_tag = "!Point"

    ## __init__
    #  Initialisation for Point
    #
    def __init__(
        self, port, mod=None, name="unknown", sd="", ld="", options=[]
    ):
        """ Initialisation for the !Point tag

        Args:
            port   : The name of the port.
            mod    : When used within a !Connect tag, or in the defaults section
                     of a !Mod, this identifies which !ModInst should be connected.
                     When used within a !Initiator or !Target tag, this identifies
                     which index of port is being referred to.
            name   : Optional name for the point.
            sd     : Short description - maximum 150 characters.
            ld     : Long description - maximum 150 characters.
            options: List of options in the form 'KEY=VAL' or just 'KEY' if no
                     value is required.
        """
        super().__init__(name, sd, ld, options)
        self.port = port
        self.mod  = mod

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: Can't validate 'port' or 'mod' as this requires knowledge of the
        #       design, this will occur during elaboration instead.
