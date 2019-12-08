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

from copy import copy

from ..schema import Reg
from ..schema.ph_tag_base import CONSTANTS as PHConstants

def modify_fields(fields, desc):
    """ Generate a new set of fields with a specified suffix.

    Args:
        fields: Lists of fields to duplicate
        desc  : Each field's description

    Returns:
        list: Set of modified fields
    """
    new_fields = []
    for field in fields:
        # NOTE: Don't use 'deepcopy' as it doesn't understand class instances.
        new_field = copy(field)
        new_field.ld = desc
        new_field.sd = desc
        new_fields.append(new_field)
    return new_fields

def perform_setclear_expansion(reg):
    """ For !Reg containing the 'setclear' option, expand the defined registers.

    Args:
        reg: The register to expand

    Returns:
        list: Set of DFRegisters that have been expanded from the input
    """
    expanded = []

    # STATUS: Readable/writeable status
    expanded.append(Reg(
        name        = reg.name,
        ld          = reg.ld,
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.RW,
        array       = reg.array,
        align       = reg.align,
        fields      = copy(reg.fields),
        options     = ["setclear=status", reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    # SET: Bitwise set register
    expanded.append(Reg(
        name        = f"{reg.name}_set",
        ld          = f"{reg.ld} (set alias - write 1 to set bit position).",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.AW,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(
            reg.fields,
            "Write a 1 to this field to set the corresponding bit (0 is ignored)."
        ),
        options     = ["setclear=set", reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    # CLEAR: Bitwise clear register
    expanded.append(Reg(
        name        = f"{reg.name}_clear",
        ld          = f"{reg.ld} (clear alias - write 1 to clear bit position).",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.AW,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(
            reg.fields,
            "Write a 1 to this field to clear the corresponding bit (0 is ignored)."
        ),
        options     = ["setclear=clear", reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    return expanded

def expand(regs):
    """
    Perform expansion of !Reg tags into set-clear register sets if they have the
    correct options present.

    Args:
        regs: The !Reg tags to expand

    Returns:
        list: Complete list of registers after the expansion (some registers may
              have been removed)
    """
    expanded = []

    # Expand any register with the option 'event'
    for reg in regs:
        clean_opts = [x.lower().strip() for x in reg.options]
        if reg.options and PHConstants.OPTIONS.SETCLEAR in clean_opts:
            expanded += perform_setclear_expansion(reg)
        else:
            expanded.append(reg)

    return expanded
