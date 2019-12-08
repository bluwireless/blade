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

def modify_fields(fields, prefix, reset=None, width=None):
    """ Generate a new set of fields with a specified prefix, reset, and width

    Args:
        fields: Lists of fields to duplicate
        prefix: The prefix for each field's description
        reset : The reset value for the field (can be a function, default: None)
        width : The width of the field (can be a function, default: None)

    Returns:
        list: Set of modified fields
    """
    new_fields = []
    for field in fields:
        # NOTE: We use a shallow copy (not deepcopy(...)) as Python doesn't
        # understand how to copy subinstances without a helper function
        new_field = copy(field)
        new_field.ld = f"{prefix} {field.ld}" if field.ld else None
        new_field.sd = f"{prefix} {field.sd}" if field.sd else None
        if reset != None:
            new_field.reset = reset(field) if callable(reset) else reset
        if width != None:
            new_field.width = width(field) if callable(width) else width
        new_fields.append(new_field)
    return new_fields

def perform_event_expansion(reg, has_mode, has_level):
    """ For !Reg containing the 'event' option, expand the defined registers.

    Args:
        reg      : The register to expand
        has_mode : Whether or not the level/edge mode register should be created
        has_level: Whether or not the level sensitivity register should be created

    Returns:
        list: Set of DFRegisters that have expanded from the input
    """
    expanded = []

    # RSTA: Raw interrupt status
    expanded.append(Reg(
        name        = f"{reg.name}_rsta",
        ld          = f"Shows unmasked (raw) interrupt event/status for {reg.ld}",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.RO,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(reg.fields, 'Raw status for'),
        options     = ['interrupt=rsta', reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    # MSTA: Masked interrupt status
    expanded.append(Reg(
        name        = f"{reg.name}_msta",
        ld          = f"Shows masked interrupt status (MSTA=RSTA & ENABLE) for {reg.ld}",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.RO,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(reg.fields, 'Masked status for'),
        options     = ['interrupt=msta', reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    # CLEAR: Clear interrupt status
    expanded.append(Reg(
        name        = f"{reg.name}_clear",
        ld          = "Clears bits in the masked (MSTA) and raw (RSTA) status registers (interrupt acknowledgement).",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.AW,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(reg.fields, 'Clear bit for'),
        options     = ['interrupt=clear', reg.name],
        location    = PHConstants.LOCATION.CORE,
        parent      = reg.name
    ))

    # ENABLE: Enable masked interrupt generation
    expanded.append(Reg(
        name        = f"{reg.name}_enable",
        ld          = "Interrupt enable. Has no effect on RSTA, but is used by MSTA & the interrupt output for the block.",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.RW,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(reg.fields, 'Enable for'),
        options     = ['interrupt=enable', reg.name],
        location    = PHConstants.LOCATION.INTERNAL,
        parent      = reg.name
    ))

    # SET: Force the interrupt RSTA state
    expanded.append(Reg(
        name        = f"{reg.name}_set",
        ld          = f"Software interrupt raise - sets bit in RSTA & MSTA (if enable set) for {reg.ld}",
        blockaccess = PHConstants.ACCESS.RO,
        busaccess   = PHConstants.ACCESS.AW,
        array       = reg.array,
        align       = reg.align,
        fields      = modify_fields(reg.fields, 'Set RSTA bit for'),
        options     = ['interrupt=set', reg.name],
        location    = PHConstants.LOCATION.CORE,
        parent      = reg.name
    ))

    # LEVEL: Configure interrupt input level sensitivity
    if has_level:
        def level_reset(field):
            # NOTE: We use a string so this can be evaluated later with scope
            return f"((1 << ({field.width})) - 1)"

        expanded.append(Reg(
            name        = f"{reg.name}_level",
            ld          = "Defines the input interrupt level sensitivity (only appropriate for interrupt generation from external sources like GPIO).",
            blockaccess = PHConstants.ACCESS.RO,
            busaccess   = PHConstants.ACCESS.RW,
            array       = reg.array,
            align       = reg.align,
            fields      = modify_fields(
                reg.fields,
                'Level mode: 0 = active low, 1 = active high. Edge mode: 0 = falling edge, 1 = rising edge.',
                reset = level_reset
            ),
            options     = ['interrupt=level', reg.name],
            location    = PHConstants.LOCATION.INTERNAL,
            parent      = reg.name
        ))

    # MODE: Configure interrupt input mode (level or edge)
    if has_mode:
        expanded.append(Reg(
            name        = f"{reg.name}_mode",
            ld          = "Defines the input interrupt mode of level or edge (only appropriate for interrupt generation from external sources like GPIO).",
            blockaccess = PHConstants.ACCESS.RO,
            busaccess   = PHConstants.ACCESS.RW,
            array       = reg.array,
            align       = reg.align,
            fields      = modify_fields(
                reg.fields, '0 = level mode, 1 = edge mode.', width=1, reset=1
            ),
            options     = ['interrupt=mode', reg.name],
            location    = PHConstants.LOCATION.INTERNAL,
            parent      = reg.name
        ))

    return expanded

def expand(regs):
    """
    Perform expansion of !Reg tags into interrupt register sets if they have the
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
        if reg.options and PHConstants.OPTIONS.EVENT in clean_opts:
            expanded += perform_event_expansion(
                reg,
                (PHConstants.OPTIONS.HAS_MODE in clean_opts),
                (
                    PHConstants.OPTIONS.HAS_LEVEL in clean_opts or
                    PHConstants.OPTIONS.NO_LEVEL not in clean_opts
                )
            )
        else:
            expanded.append(reg)

    return expanded
