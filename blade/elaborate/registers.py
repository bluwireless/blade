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

import ctypes
import os

# Get hold of the report
from .. import reporting
report = reporting.get_report("elaborator.registers")

from .common import ElaborationError, options_to_attributes, tag_source_info

from ..schema import Config, Define, Field, Group, Macro, Reg, Register
from ..schema.ph_tag_base import CONSTANTS as PHConstants
from designformat import DFConstants, DFRegister, DFRegisterField, DFRegisterGroup

# Import all of the available expansions
from . import register_interrupt
from . import register_setclear
all_expansions = [
    register_interrupt.expand,
    register_setclear.expand
]

def resolve_xref(xref=[], ref=None, scope=None, ctx={}):
    """
    Resolve a value cross-reference of the form '<group>/<reg>/<field>/<param>'.
    Note that the modified context allows 'self' to be resolved in nested references

    Args:
        xref : Tuple of items identifying a cross-referenced parameter
        ref  : Identifier of a referenced parameter on this instance (not used)
        scope: The ElaboratorScope object for wider-crossreferencing
        ctx  : Context to use for resolving the cross-reference

    Returns:
        tuple: Tuple of the value of the crossreference and a modified context
    """
    group = None
    focus = None

    # Pop the last item (the parameter)
    last = xref.pop()

    # NOTE: Part #0: group, #1: register, #2: field, #3 parameter
    # Find the group being referenced - always present
    if xref[0].lower() == "self":
        if not 'group' in ctx or not ctx['group']:
            raise ElaborationError(
                report.error(f"No !Group provided to resolve reference: {'/'.join(xref)}")
            )
        group = ctx['group']
    else:
        group = scope.get_document(xref[0], Group)
        if not group:
            raise ElaborationError(report.error(f"Could not find !Group {xref[0]}"))

    # Focus on the register being referenced (optional)
    focus = group
    if len(xref) > 1:
        found = [x for x in focus.regs if x.name == xref[1]]
        if len(found) != 1:
            raise ElaborationError(
                report.error(
                    f"Could not resolve !Reg {xref[1]} within !Group {focus.name}",
                    item=focus
                ),
                ph_doc=focus
            )
        focus = found[0]

        # Focus on the field being referenced (optional)
        if len(xref) > 2:
            found = [x for x in focus.fields if x.name == xref[2]]
            if len(found) != 1:
                raise ElaborationError(
                    report.error(
                        f"Could not resolve !Field {xref[2]} within !Reg {focus.name}",
                        item=focus
                    ),
                    ph_doc=focus
                )
            focus = found[0]

    # Get the value from the focused item
    value = focus.__getattribute__(last)

    # We need to check and see if there is a !Define override on this value
    relevant = []
    if xref[0] in ctx['defs']: # Group
        if len(xref) > 1 and xref[1] in ctx['defs'][xref[0]]: # Register
            if len(xref) > 2 and xref[2] in ctx['defs'][xref[0]][xref[1]]: # Field
                relevant = ctx['defs'][xref[0]][xref[1]][xref[2]]["!Define"]
            else:
                relevant = ctx['defs'][xref[0]][xref[1]]["!Define"]
        else:
            relevant = ctx['defs'][xref[0]]["!Define"]

    for item in relevant:
        if hasattr(item, last) and item.__getattribute__(last) != None:
            value = item.__getattribute__(last)

    # Return the value
    return (value, { "group": group, "defs": ctx['defs'] })

def build_register(
    group, reg, address, iteration, scope, defs_scope, m_prefix=None
):
    """
    Evaluate a !Reg into an instance of DFRegister, handling different naming
    conventions depending whether or not it is being generated under a !Macro.

    Args:
        group     : The !Group tag containing this register.
        reg       : The !Reg tag to evaluate
        address   : The address the register has been placed at
        iteration : The current iteration we're on (!Reg.array can be > 1)
        scope     : The ElaboratorScope object
        defs_scope: Hierarchical scope of !Define values related to this group
        m_prefix  : Prefix for registers created by a macro (default: None)

    Returns:
        DFRegister: The constructed register
    """
    # Identify the filename of the register definition
    file = ""
    if reg.source and reg.source.path and len(reg.source.path) > 0:
        file = os.path.basename(reg.source.path)

    # Define functions for easy resolution of !Reg/!Field parameters, taking into
    # account !Define overrides, and evaluating any expressions/cross-references
    def reg_param(param=None, value=None, do_eval=True, default=None):
        value = reg.__getattribute__(param) if param != None else value
        # Check for this parameter in scoped defines
        if (
            (param      != None                  ) and
            (group.name in defs_scope            ) and
            (reg.name   in defs_scope[group.name]) and
            (len(defs_scope[group.name][reg.name]["!Define"]) > 0)
        ):
            for define in defs_scope[group.name][reg.name]["!Define"]:
                if hasattr(define, param) and define.__getattribute__(param) not in [None, '']:
                    value = define.__getattribute__(param)
                    break
        # If value is None, substitute the default
        if value == None:
            value = default
        # Perform evaluation if required
        if value != None and do_eval:
            return scope.evaluate_expression(
                value,
                ref_cb=resolve_xref, ref_ctx={"group": group, "defs": defs_scope}
            )
        else:
            return value

    def field_param(field, param=None, value=None, do_eval=True, default=None):
        assert isinstance(field, Field)
        value = field.__getattribute__(param) if param != None else value
        # Check for this parameter in scoped defines
        if (
            (param      != None                            ) and
            (group.name in defs_scope                      ) and
            (reg.name   in defs_scope[group.name]          ) and
            (field.name in defs_scope[group.name][reg.name]) and
            (len(defs_scope[group.name][reg.name][field.name]["!Define"]) > 0)
        ):
            for define in defs_scope[group.name][reg.name][field.name]["!Define"]:
                if hasattr(define, param) and define.__getattribute__(param) not in [None, '']:
                    value = define.__getattribute__(param)
                    break
        # If value is None, substitute the default
        if value == None:
            value = default
        # Perform evaluation if required
        if value != None and do_eval:
            return scope.evaluate_expression(
                value,
                ref_cb=resolve_xref, ref_ctx={"group": group, "defs": defs_scope}
            )
        else:
            return value

    # Build the name
    reg_name = f"{reg.name.strip()}_{iteration}"
    if m_prefix != None:
        reg_name = f"{m_prefix.strip()}_{reg_name}"

    # Evaluate the width
    reg_width = reg_param('width', default=32)

    # Sum up the field widths and check for MAC_CMD marker, this modifies the
    # behaviour so that the expected register width is not 32
    total_width = 0
    has_command = False
    for field in reg.fields:
        total_width += field_param(field, 'width', default=1)
        has_command |= (field.type == PHConstants.FIELD_TYPES.CMD_DEF)

    if has_command:
        reg_width = total_width

    # Determine the access modes allowed
    bus_access   = reg_param('busaccess',   do_eval=False, default=DFConstants.ACCESS.RW)
    block_access = reg_param('blockaccess', do_eval=False, default=DFConstants.ACCESS.RW)
    inst_access  = reg_param('instaccess',  do_eval=False, default=DFConstants.ACCESS.RO)

    # Create the register
    df_reg = DFRegister(
        reg_name, address, bus_access, block_access, inst_access,
        description=(reg_param('ld', do_eval=False) if reg.ld else reg_param('sd', do_eval=False))
    )

    # Append any options
    options_to_attributes(reg, df_reg)

    # Store the location as an attribute
    df_reg.setAttribute('location', reg.location)

    # Store the parent as an attribute
    df_reg.setAttribute('parent', reg.parent)

    # Store the protection field as an attribute
    df_reg.setAttribute('protect', reg_param('protect', do_eval=False, default="000"))

    # Build a bitmap to track if register fields clash
    bitmap   = [None for x in range(reg_width)]

    # Track which bit is next to be allocated (allows spacing to be created
    # between fields where later fields are automatically placed).
    next_lsb = 0

    # Attach register fields
    for field in reg.fields:
        # Pickup if the register requests a specific LSB or MSB
        req_lsb = field_param(field, 'lsb')
        req_msb = field_param(field, 'msb')

        # Keep track of the width, reset value and allocated LSB
        width = field_param(field, 'width', default=1)
        reset = field_param(field, 'reset', default=0)
        lsb   = req_lsb if req_lsb != None else next_lsb

        # If the width has evaluated to 0, warn and skip
        if width == 0:
            report.warning(f"!Field {file}: {reg_name}.{field.name} has zero width")
            continue

        # Check LSB is not negative
        if lsb < 0:
            raise ElaborationError(
                report.error(
                    f"!Field {file}: {reg_name}.{field.name} cannot be placed, LSB is invalid",
                    item=field
                ),
                ph_doc=field
            )

        # If the reset value is negative and we're not signed, wrap it correctly
        while reset < 0:
            reset += (1 << width)

        # Check LSB & MSB are compatible (if both specified)
        if req_lsb != None and req_msb != None:
            if (req_msb - width + 1) != req_lsb:
                raise ElaborationError(
                    report.error(
                        f"!Field {file}: {reg_name}.{field.name} LSB {req_lsb}"
                        f" and MSB {req_msb} don't agree",
                        item=field
                    ),
                    ph_doc=field
                )
        elif req_msb != None:
            lsb = (req_msb - width + 1)

        # Check if there is space in the bitmap
        if len([x for x in bitmap[lsb:] if x == None]) < width:
            # TODO: Should throw exception, but we need to change YAML first
            report.warning(
                f"!Field {file}: {reg_name}.{field.name} exceeds maximum width ({len(bitmap)})"
            )
            # TEMP: Extend the bitmap to accomodate the extra fields
            for bit in range(reg_width, lsb+width):
                bitmap.append(None)
        # Check for overlaps between fields
        elif len([x for x in bitmap[lsb:(lsb+width)] if x != None]) > 0:
            raise ElaborationError(
                report.error(
                    f"!Field {file}: {reg_name}.{field.name} overlaps with: " +
                    ", ".join([x.name for x in bitmap[lsb:(lsb+width)] if x != None]),
                    item=field
                ),
                ph_doc=field
            )

        # Reserve the slot in the bitmap for this field
        for i in range(width):
            bitmap[i+lsb] = field

        # Update where the next free LSB is
        rem_bitmap = bitmap[(lsb + width):]
        next_lsb   = (rem_bitmap.index(None) + (lsb + width)) if None in rem_bitmap else -1

        # Create the register field
        report.debug(f"Adding field '{field.name}' with LSB={lsb} and WIDTH={width}")
        df_field = DFRegisterField(
            field.name, lsb, width, reset,
            signed      = (field.type == PHConstants.FIELD_TYPES.S),
            description = (field.ld if field.ld and len(field.ld.strip()) > 0 else field.sd)
        )
        df_reg.addField(df_field)

        # Append any enumerated values
        enum_list = field_param(field, 'enums', do_eval=False)
        if enum_list:
            enum_val = -1
            for enum in enum_list:
                # Pickup if a value has been defined
                if enum.val != None:
                    tmp_val = scope.evaluate_expression(
                        enum.val, ref_cb=resolve_xref,
                        ref_ctx={"group": group, "defs": defs_scope}
                    )
                    enum_val = tmp_val if tmp_val != None else (enum_val + 1)
                # Automatically enumerate previous value
                else:
                    enum_val += 1
                # Check if the value goes outside of the width of this field
                if enum_val > ((1 << width) - 1):
                    report.warning(
                        f"Enumeration value for !Field ({file}) {reg_name}.{field.name}"
                        f" exceeds width ({width} bits) of field: {enum.name}={enum_val}"
                    )
                # Store the field
                df_field.addEnumValue(enum.name, enum_val, enum.ld if enum.ld else enum.sd)

        # Append any options
        options_to_attributes(field, df_field)

        # If this field has type of 'CMD_DEF', set an attribute
        # TODO: This is used by MAC_CMD_DEFINES, should use a dedicated !Command
        #       tag - but this requires modifying the schema.
        if field.type == PHConstants.FIELD_TYPES.CMD_DEF:
            df_field.setAttribute('CMD_DEF', True)

    # Detect and warn if the field order differs from the declaration order
    placed = []
    for x in bitmap:
        if x != None and x not in placed:
            placed.append(x)

    for i in range(len(placed) if len(placed) >= len(reg.fields) else len(reg.fields)):
        expected = reg.fields[i].name if i < len(reg.fields) else ""
        reality  = placed[i].name     if i < len(placed) else ""
        if expected != reality:
            report.warning(
                f"!Field {file}: {reg_name}.{expected} LSB placement differs "
                f"from declared order"
            )

    # Return the register
    return df_reg

def build_group(
    group, is_macro, next_addr, scope, defs_scope,
    m_prefix=None, m_array=None, m_align=None
):
    """
    Expand a !Group into a set of DFRegisters, taking account of the 'array' value
    to expand multiple instances. Returns a list of DFRegisterGroups - one per
    group instance.

    Args:
        group     : The group to expand
        is_macro  : Whether this group has been declared as a macro
        next_addr : The next free byte-address to allocate
        scope     : The ElaboratorScope object for resolving references
        defs_scope: Hierarchical scope of !Define values related to this group
        m_prefix  : Prefix for registers when evaluating a macro (default: None)
        m_array   : Number of instances when evaluating a macro (default: None)
        m_align   : Alignment of each instance when evaluating a macro (default: None)

    Returns:
        tuple: Tuple of the constructed DFRegisterGroup and the next free address
    """
    # Identify the filename of the group definition
    file = ""
    if group.source and group.source.path and len(group.source.path) > 0:
        file = os.path.basename(group.source.path)

    # Define functions for easy resolution of !Group/!Reg parameters, taking into
    # account !Define overrides, and evaluating any expressions/cross-references
    def group_param(param=None, value=None, do_eval=True, default=None):
        value = group.__getattribute__(param) if param != None else value
        # Check for this parameter in scoped defines
        if (
            (param      != None      ) and
            (group.name in defs_scope) and
            (len(defs_scope[group.name]["!Define"]) > 0)
        ):
            for define in defs_scope[group.name]["!Define"]:
                if hasattr(define, param) and define.__getattribute__(param) not in [None, '']:
                    value = define.__getattribute__(param)
                    break
        # If value is None, substitute the default
        if value == None:
            value = default
        # Perform evaluation if required
        if value != None and do_eval:
            return scope.evaluate_expression(
                value, ref_cb=resolve_xref, ref_ctx={"group": group, "defs": defs_scope}
            )
        else:
            return value

    def reg_param(reg, param=None, value=None, do_eval=True, default=None):
        assert isinstance(reg, Reg)
        value = reg.__getattribute__(param) if param != None else value
        # Check for this parameter in scoped defines
        if (
            (param      != None                  ) and
            (group.name in defs_scope            ) and
            (reg.name   in defs_scope[group.name]) and
            (len(defs_scope[group.name][reg.name]["!Define"]) > 0)
        ):
            for define in defs_scope[group.name][reg.name]["!Define"]:
                if hasattr(define, param) and define.__getattribute__(param) not in [None, '']:
                    value = define.__getattribute__(param)
                    break
        # If value is None, substitute the default
        if value == None:
            value = default
        # Perform evaluation if required
        if value != None and do_eval:
            return scope.evaluate_expression(
                value, ref_cb=resolve_xref, ref_ctx={"group": group, "defs": defs_scope}
            )
        else:
            return value

    # Check we are doing something sensible
    report.debug("Running sanity checks on group")
    if not isinstance(group, Group):
        raise ElaborationError(
            report.error(
                f"Trying to expand non-!Group tag of type {type(group)} ({file})",
                item=group
            ),
            ph_doc=group
        )
    elif is_macro and group.type != PHConstants.GROUP_TYPES.MACRO:
        raise ElaborationError(
            report.error(
                f"Evaluating Macro but group {group.name} is not of MACRO type ({file})",
                item=group
            ),
            ph_doc=group
        )
    elif not is_macro and group.type != PHConstants.GROUP_TYPES.REGISTER:
        raise ElaborationError(
            report.error(
                f"Evaluating non_Macro but group {group.name} is not of REGISTER type ({file})",
                item=group
            ),
            ph_doc=group
        )

    # Determine the array and alignment values
    # TODO: If !Group tag's 'array' attribute is deprecated, remove support
    grp_array    = group_param(value=m_array) if is_macro else group_param('array', default=1)
    byte_mode    = PHConstants.OPTIONS.BYTE in (x.lower() for x in group.options)
    # NOTE: When not in byte mode, alignments and addresses are in terms of words
    align        = group_param(value=m_align) if is_macro else 1
    byte_align   = align if byte_mode else (align << 2)
    align_mask   = (byte_align - 1)
    i_align_mask = ctypes.c_uint32(~align_mask).value

    # Expand the register set by passing it through expansions
    report.debug("Running register expansions")
    all_regs = group.regs
    for expansion in all_expansions:
        report.debug(f"Expansion: {expansion.__name__}")
        all_regs = expansion(all_regs)

    # If alignment is required for the group, apply the constraint
    # NOTE: Only the first pass of the group is aligned, repeats follow directly
    if align != None:
        if (next_addr & align_mask) != 0:
            next_addr = (next_addr + byte_align) & i_align_mask

    # For each count of array, repeat the instantiation
    df_groups = []
    report.debug(f"Expanding group {group.name} {grp_array} times:")
    for i_group in range(grp_array):
        # Create the new group, only include the index in the group name if it
        # is being repeated more than once
        grp_name = m_prefix if is_macro else group.name
        if grp_array > 1: grp_name += f"_{i_group}"
        df_group = DFRegisterGroup(
            id          = grp_name,
            offset      = next_addr,
            description = group_param('ld', do_eval=False) if group.ld != None else group_param('sd', do_eval=False)
        )

        # Append any options
        options_to_attributes(group, df_group)

        # Forward the 'MACRO' marker through
        if is_macro:
            df_group.setAttribute('MACRO', group.name)

        # Tag where this group came from
        tag_source_info(group, df_group)

        # Process every !Reg into a DFRegister
        for reg in all_regs:
            if not isinstance(reg, Reg):
                raise ElaborationError(
                    report.error(
                        f"Trying to evaluate non-!Reg tag of type {type(reg)}",
                        item=reg
                    ),
                    ph_doc=reg
                )

            # Evaluate how many instances of this register there are
            reg_array = int(reg_param(reg, 'array', default=1))

            # Evaluate width of this register (consistent over instances)
            reg_width      = reg_param(reg, 'width', default=1)
            reg_byte_width = int((reg_width + 7) / 8)

            # Work out the base address for this array
            reg_address      = next_addr
            reg_align        = reg_param(reg, 'align', default=1)
            reg_byte_align   = reg_align if byte_mode else (reg_align << 2)
            reg_align_mask   = (reg_byte_align - 1)
            reg_i_align_mask = ctypes.c_uint32(~reg_align_mask).value

            # If the register specifies an address, then adopt it
            # NOTE: When not in byte mode, addresses are specified in words not bytes
            if reg.addr != None and len(str(reg.addr).strip()) != 0:
                reg_address = reg_param(reg, 'addr')
                if not byte_mode: reg_address *= 4

            # Ensure the register address isn't out-of-sequence
            if reg_address < next_addr:
                raise ElaborationError(
                    report.error(
                        f"Address for '{reg.name}' out of sequence "
                        f"({hex(reg_address)} < {hex(next_addr)}) ({file})",
                        item=reg
                    ),
                    ph_doc=reg
                )

            # Create each instance of the register
            for i_reg in range(reg_array):
                report.debug(
                    f"Creating register '{reg.name}[{i_reg}]' @ {hex(reg_address)}",
                    ph_doc=reg
                )

                # Ensure that the alignment constraint is satifisfied
                if (reg_address & reg_align_mask) != 0:
                    reg_address = (reg_address + reg_byte_align) & reg_i_align_mask

                # Build this register (using offset relative to the group)
                df_group.addRegister(build_register(
                    group, reg, # Pass the group so that we can cross-reference
                    (reg_address - df_group.offset), i_reg, scope, defs_scope,
                    m_prefix=(grp_name if is_macro else None)   # Macro prefix
                ))

                # Bump the address onwards by the width of this register
                reg_address += reg_byte_width

                # Ensure we are aligned to a word boundary
                if not byte_mode and (reg_address & 0x3) != 0:
                    reg_address = (reg_address + 4) & 0xFFFFFFFC

            # Update the next address
            next_addr = reg_address

        # Add the DFRegisterGroup to the list of generated groups
        df_groups.append(df_group)

    # Return a tuple of the register group and the next free address
    return (df_groups, next_addr)

def elaborate_registers(top, scope, max_depth=None):
    """
    Evaluate either a !Config expanding into a list of registers. !Registers or
    !Macros considered in the order specified in the !Config.

    Args:
        top      : The top-level !Config tags to evaluate
        scope    : An ElaboratorScope object containing all documents included
                   directly or indirectly by the top module.
        max_depth: Ignored for now

    Returns:
        list: List of all constructed DFRegisterGroups
    """
    if not isinstance(top, Config):
        raise ElaborationError(
            report.error(
                f"Expected !Config, got {type(top).__name__}", item=top
            ),
            ph_doc=top
        )

    # Separate the !Define overrides into separate scopes for groups and macros
    defines = []
    if top.source != None:
        defines = [x for x in top.source.get_parsed_documents() if isinstance(x, Define)]
    group_defs = {}
    macro_defs = {}

    for item in defines:
        defs_dict = None
        if item.group == 'MACRO':
            if not item.name in macro_defs:
                macro_defs[item.name] = { "!Define": [] }
            defs_dict = macro_defs[item.name]
        else:
            if not item.group in group_defs:
                group_defs[item.group] = { "!Define": [] }
            defs_dict = group_defs[item.group]
        if item.reg:
            if not item.reg in group_defs[item.group]:
                defs_dict[item.reg] = { "!Define": [] }
            if item.field:
                if not item.field in defs_dict:
                    defs_dict[item.reg][item.field] = { "!Define": [] }
                defs_dict[item.reg][item.field]["!Define"].append(item)
            else:
                defs_dict[item.reg]["!Define"].append(item)
        else:
            defs_dict["!Define"].append(item)

    # Work through the !Config, processing normal and macro type groups
    next_address = 0
    all_groups   = []
    for item in top.order:
        report.debug(f"Elaborating {type(item).__name__}: {item.name}")
        if isinstance(item, Register):
            resolved = scope.get_document(item.group, expected=Group)
            if not resolved:
                raise ElaborationError(
                    report.error(
                        f"Could not resolve register group: {item.group}",
                        item=item
                    ),
                    ph_doc=item
                )
            (reg_groups, next_address) = build_group(
                resolved, False, next_address, scope, group_defs,
            )
            all_groups += reg_groups
        elif isinstance(item, Macro):
            resolved = scope.get_document(item.macro, expected=Group)
            # Check if there are !Define overrides for this macro
            m_array = item.array
            m_align = item.align
            if item.name in macro_defs and len(macro_defs[item.name]["!Define"]) > 0:
                for define in macro_defs[item.name]["!Define"]:
                    if isinstance(define.array, int) or define.array:
                        m_array = define.array
                    if isinstance(define.align, int) or define.align:
                        m_align = define.align
            # Evaluate array & align to expand variables
            m_array = scope.evaluate_expression(
                m_array, ref_cb=resolve_xref,
                ref_ctx={ "group": resolved, "defs": macro_defs }
            )
            m_align = scope.evaluate_expression(
                m_align, ref_cb=resolve_xref,
                ref_ctx={ "group": resolved, "defs": macro_defs }
            )
            # Build the group
            (reg_groups, next_address) = build_group(
                resolved, True, next_address, scope, macro_defs,
                m_prefix=item.name, m_array=m_array, m_align=m_align
            )
            all_groups += reg_groups
        else:
            raise ElaborationError(
                report.error(
                    f"Invalid type referenced in order: {type(resolved)}",
                    item=resolved
                ),
                ph_doc=resolved
            )

    # Return all constructed DFRegisterGroups
    return all_groups
