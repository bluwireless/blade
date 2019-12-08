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
As a primitive tag type, a !HisRef can be declared using either mapping or
sequence syntax - the sample example is shown below in both styles:

.. highlight:: yaml
.. code-block:: yaml

    - !HisRef [my_ref, my_his, "Double instance", 2, Slave, "Longer description...", []]

    - !HisRef
      name   : my_ref
      ref    : my_his
      sd     : Double instance
      count  : 2
      role   : master
      ld     : Longer description...
      options: []

"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.hisref")

class HisRef(TagBase):
    """ Instantiates a pre-defined !His as a signal component or boundary port """
    yaml_tag = "!HisRef"

    def __init__(
        self, name, ref, sd="", count=1, role="master", ld="", options=[]
    ):
        """ Initialisation for the !HisRef YAML tag

        Args:
            name   : Name of the port
            ref    : The defined !His being instantiated
            sd     : Short description of the component - maximum 150 characters
            count  : Number of reptitions of this component
            role   : Role for this instance, either 'master' or 'slave'
            ld     : Long description of the instantiation
            options: List of options either in the form 'KEY=VAL' or just 'KEY'
                     if a value is not required
        """
        super().__init__(name, sd, ld, options)
        self.ref   = ref
        self.count = count
        self.role  = role.strip().upper() if isinstance(role, str) else role

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # NOTE: We can't validate 'ref' yet as that requires knowledge of His

        # Check that 'count', if non-complex, is integer and positive
        if str(self.count).strip().replace(".","").isdigit():
            if "." in str(self.count):
                raise ValidationError(
                    report.error("HisRef count value must be integer", self=item),
                    "count", self
                )
            elif int(self.count) <= 0:
                raise ValidationError(
                    report.error("HisRef count value must be >= 1", self=item),
                    "count", self
                )

        # Check that 'role' is in the list of supported options
        if not self.role in CONSTANTS.ROLES:
            raise ValidationError(
                report.error(f"HisRef specifies an unsupported role {self.role}", self=item),
                "role", self
            )
