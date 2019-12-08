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
As the !ModInst tag is primitive, it can be used with either mapping or sequence
syntax - although the latter is encouraged for brevity. An example of both uses
is given below:

.. highlight:: yaml
.. code-block:: yaml

    - !Mod
      name   : my_mod
      modules:
      - !ModInst [block_a, inverter, "Instantiating 4 inverters", 4]
      - !ModInst
        name : block_b
        ref  : adder
        sd   : Instantiating 2 addition units
        count: 2
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.mod_inst")

class ModInst(TagBase):
    """ Instantiates a !Mod description with a name and count """
    yaml_tag = "!ModInst"

    def __init__(self, name, ref, sd="", count=1, ld="", options=[]):
        """ Initialisation for !ModInst tag.

        Args:
            name   : Name of the instantiation
            ref    : The !Mod tag to instantiate
            sd     : Short description - maximum 150 characters
            count  : How many instances to create
            ld     : Long description - no maximum length
            options: List of options either in the form 'KEY=VALUE' or just 'KEY'
                     if a value is not required.
        """
        super().__init__(name, sd, ld, options)
        self.ref        = ref
        self.count      = count

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: Can't validate 'ref' as that requires knowledge of !Mods

        # Check that 'count', if non-complex, is integer and positive
        if str(self.count).strip().replace(".","").isdigit():
            if "." in str(self.count):
                raise ValidationError(
                    report.error("Port count value must be integer", self=item),
                    "count", self
                )
            elif int(self.count) <= 0:
                raise ValidationError(
                    report.error("Port count value must be >= 1", self=item),
                    "count", self
                )
