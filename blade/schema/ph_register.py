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
As the !Register tag only takes a single attribute (the !Group name) it is far
easier to use sequence syntax rather than the mapping style, although both are
legal syntax.

.. highlight:: yaml
.. code-block:: yaml

    - !Config
      order:
      - !Register [group_a]
      - !Register
        group: group_b

    - !Group
      name: group_a
      ...

    - !Group
      name: group_b
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.register")

class Register(TagBase):
    """
    A !Register is a tag used within a !Config to specify the order of processing
    of defined groups. Without a !Config attribute, groups are expanded in the
    order that they're declared.
    """
    yaml_tag = "!Register"

    def __init__(self, group):
        """ Initialisation for the !Register tag

        Args:
            group: The name of the !Group that is being instantiated
        """
        super().__init__(None, None, None, None)
        self.group = group

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'group' is a non-zero length string, it's not possible to
        # perform further validation at this point as we're unaware of other tags
        if not isinstance(self.group, str) or len(self.group.strip()) == 0:
            raise ValidationError(
                report.error("Register does not define a group", item=self),
                "group", self
            )
