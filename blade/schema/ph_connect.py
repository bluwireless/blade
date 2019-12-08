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
The !Connect tag can either be used to express interconnectivity between ports
or to tie a port to a constant value - examples of both modes are given below:

.. highlight:: yaml
.. code-block:: yaml

    - !Mod
      name   : my_mod
      ports  :
      - !HisRef [switch_on, enable, "Control to switch on blocks",    1, Slave]
      - !HisRef [output,    wire,   "Output signals from each block", 4, Master]
      modules:
      - !ModInst [block_a,   inverter, "Inverts value", 1]
      - !ModInst [block_b,   and,      "ANDs values",   1]
      - !ModInst [or_blocks, or,       "ORs values",    2]
      connections:
      - !Connect
        points:
        - !Point [switch_on]
        - !Point [enable, block_a]
        - !Point [enable, block_b]
        - !Point [enable, or_blocks]
      - !Connect
        const:
        - !Point [input, block_a]
        - !Const [1]
      - !Connect
        const:
        - !Point [output, block_a]
        - !Point [output, block_b]
        - !Point [output, or_blocks]
        - !Point [output]
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.connect")

# For validation
from .ph_point import Point
from .ph_const import Const

class Connect(TagBase):
    """
    The !Connect tag represents an interconnection between ports of different
    blocks, it can also be used to tie-off signals to a constant value.
    """
    yaml_tag = "!Connect"

    def __init__(
        self, points=[], name="unknown", sd="", ld="", options=[], constants=[]
    ):
        """ Initialisation for the Connect tag.

        Args:
            points   : List of !Point tags to connect.
            name     : Optional for the connection.
            sd       : Short description - maximum 150 characters.
            ld       : Long description - no maximum length.
            options  : List of options in the form 'KEY=VAL' or just 'KEY' if a
                       value is not required.
            constants: List containing !Points and a single !Const tag in order
                       to tie a signal to a specific value.
        """
        super().__init__(name, sd, ld, options)
        self.points    = points
        self.constants = constants

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for point in self.points:
            point.set_source_file(file)
        for constant in self.constants:
            constant.set_source_file(file)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'points' is a list only containing Point objects
        if self.points != None:
            if not isinstance(self.points, list):
                raise ValidationError(
                    report.error("Connect points are not stored as a list", item=self),
                    "points", self
                )
            bad = [x for x in self.points if not isinstance(x, Point)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Connect points contains {bad[0].yaml_tag}", item=self),
                    "points", self
                )
            # Validate all points
            for point in self.points:
                point.validate()

        # Check that 'constants' is a list only containing Point and Const objects
        if self.constants != None:
            if not isinstance(self.constants, list):
                raise ValidationError(
                    report.error("Connect constants are not stored as a list", item=self),
                    "constants", self
                )
            bad = [x for x in self.constants if not isinstance(x, Point) and not isinstance(x, Const)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Connect constants contains {bad[0].yaml_tag}", item=self),
                    "constants", self
                )
            # Validate all Point and Const objects
            for item in self.constants:
                item.validate()

class Conect(Connect):
    """
    Provide legacy support for the '!Conect' tag - this is just an alias over
    the '!Connect' tag class for backwards compatibility.
    """
    yaml_tag = "!Conect"

    # TODO: Provide warning on initialisation of deprecation?
