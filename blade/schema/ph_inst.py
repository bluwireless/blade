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

    - Inst
      name  : root
      sd    : Base instruction from which everything extends
      fields:
      - !Field
        name : class
        lsb  : 0
        width: 5
        enums:
        - !Enum [load_store, 0]
        - !Enum [math,       1]
        - !Enum [logic,      2]

    - !Inst
      name    : load_store
      base    : root
      decode_f: class
      decode_e: load_store
      fields  :
      - !Field
        name : operation
        lsb  : 5
        width: 2
        enums:
        - !Enum [load,  0]
        - !Enum [store, 1]
        - !Enum [clear, 2]
      - !Field
        name : operand_1
        lsb  : 7
        width: 5
      ...

    - !Inst
      name    : load_to_reg
      base    : load_store
      decode_f: operation
      decode_e: load
      fields  :
      - !Field
        name : register
        lsb  : 12
        width: 5
      ...
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.inst")

# For validation
from .ph_field import Field

class Inst(TagBase):
    """
    Declares an instruction that can be extended to create a similarly formed
    instruction set, where the value of an inherited field can be forced to a
    specific value.
    """

    yaml_tag = "!Inst"

    ## __init__
    #  Initialisation for Inst
    #
    def __init__(
        self,
        name,
        base="",
        decode_f="",
        decode_e="",
        options="",
        sd="",
        ld="",
        hir_ref="",     # TODO: Deprecated - remove?
        hir_name="",    # TODO: Deprecated - remove?
        fields=None,
        unrolled=None,  # TODO: Deprecated - remove?
    ):
        """ Initialisation for the !Inst tag.

        Args:
            name    : Name of the instruction
            base    : Instruction to inherit from
            decode_f: Which field should be fixed to a certain value
            decode_e: What value from the enumeration of the field referenced by
                      decode_f should be taken
            options : List of options in the form 'KEY=VAL' or just 'KEY' if a
                      value is not required
            sd      : Short description - maximum 150 characters
            ld      : Long description - no limit on length
            hir_ref : Deprecated field - will be removed
            fields  : List of !Field tags for the instruction
            unrolled: Deprecated field - will be removed
        """
        super().__init__(name, sd, ld, options)
        self.base     = base
        self.decode_f = decode_f
        self.decode_e = decode_e
        self.fields   = fields
        self.unrolled = unrolled
        self.hir_name = hir_name
        self.hir_ref  = hir_ref

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for field in self.fields:
            field.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for field in self.fields:
            if self.start_mark:
                field.shift_file_marks(start.line - self.start_mark.line)
            else:
                field.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'fields' is a list only containing Field objects
        if self.fields != None:
            if not isinstance(self.fields, list):
                raise ValidationError(
                    report.error("Inst fields are not stored as a list", item=self),
                    "fields", self
                )
            bad = [x for x in self.fields if not isinstance(x, Field)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Inst fields contains {bad[0].yaml_tag}", item=self),
                    "fields", self
                )
            # Validate all fields
            for field in self.fields:
                field.validate()
