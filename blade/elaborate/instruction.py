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

# Get hold of the report
from .. import reporting
report = reporting.get_report("elaborator.instruction")

from .common import ElaborationError, options_to_attributes, tag_source_info

from ..schema import Enum, Field, Inst
from ..schema.ph_tag_base import CONSTANTS as PHConstants
from designformat import DFConstants, DFCommand, DFCommandField

def resolve_xref(xref=[], ref=None, scope=None, ctx={}):
    """
    Resolve a value cross-reference either of the form '<inst>/<field>/<param>'
    or of the form '$param' (for reading other fields in the same object). Note
    that the modified context allows 'self' to be resolved in nested references.

    Args:
        xref : Tuple of items identifying a cross-referenced parameter
        ref  : Identifier of a referenced parameter on this instance (self-ref)
        scope: The ElaboratorScope object for wider-crossreferencing
        ctx  : Context to use for resolving the cross-reference

    Returns:
        tuple: Tuple of the crossreferenced value and a modified context
    """
    inst  = ctx['inst']
    field = ctx['field'] if 'field' in ctx else None
    focus = None
    param = None

    if not 'inst' in ctx or not ctx['inst']:
        raise ElaborationError(report.error(
            f"No !Inst provided to resolve reference {ref if ref else '/'.join(xref)}"
        ))

    # For a self-reference (e.g. '$msb'), focus on this object
    if ref != None:
        # NOTE: The local context can either be a !Inst or a !Field
        focus = ctx['field'] if 'field' in ctx else ctx['inst']
        param = ref
    # For a cross-reference, chase the parameter hierarchically
    else:
        # For a cross-reference, the parameter is the last element
        param = xref.pop()
        # Find the instruction being referenced
        if xref[0].lower() != "self":
            inst = scope.get_document(xref[0], Inst)
            if not inst:
                raise ElaborationError(report.error(f"Could not find !Inst {xref[0]}"))
        focus = inst

        # Focus on the field being referenced (optional)
        if len(xref) > 1:
            found = [x for x in focus.fields if x.name == xref[1]]
            if len(found) != 1:
                raise ElaborationError(
                    report.error(
                        f"Could not resolve !Field {xref[1]} within !Inst {focus.name}",
                        item=focus
                    ),
                    ph_doc=focus
                )
            field = found[0]
            # Move the focus
            focus = field

    # Get the value from the focused item
    value = focus.__getattribute__(param)

    # Return the value
    return (value, {"inst": inst, "field": field})

def resolve_instruction(inst, scope):
    """
    As !Inst have the ability to extend from other !Inst, this function resolves
    the instruction hierarchy and returns the inherited set of fields. It also
    takes into account 'decode_f' and 'decode_e' to fix values in inherited
    fields. Note this function can be called recursively with nested references.

    Args:
        inst : The instruction to resolve
        scope: The ElaboratorScope object to use to resolve references
    """
    # If this instruction inherits, resolve the referenced instruction first. We
    # also build up a hierarchical name for the instruction.
    name     = inst.name
    basename = None
    fields   = []
    if inst.base:
        base = scope.get_document(inst.base, expected=Inst)
        if not base:
            raise ElaborationError(
                report.error(
                    f"Could not resolve base instruction '{inst.base}'",
                    item=inst
                ),
                ph_doc=inst
            )
        (basename, tmp_base, res_fields) = resolve_instruction(base, scope)
        fields += res_fields

    # Work through the fields, where one matches 'decode_f' we modify it
    propagated = []
    found_dc_f = False
    for field in fields:
        if inst.decode_f and inst.decode_f.strip() == field.name.strip():
            found_dc_f = True
            mod_field  = copy(field)
            if inst.decode_e:
                val_match = [x for x in mod_field.enums if inst.decode_e.strip() == x.name.strip()]
                if len(val_match) != 1:
                    raise ElaborationError(
                        report.error(
                            f"Could not resolve decode_e '{inst.decode_e}' in field '{field.name}'",
                            item=inst
                        ),
                        ph_doc=inst
                    )
                # Evaluate the value for reset
                value = scope.evaluate_expression(
                    val_match[0].val, ref_cb=resolve_xref, ref_ctx={"inst": inst, "field": field}
                )
                mod_field.reset       = value
                mod_field.description = str(value)
                mod_field.options.append('value_fixed')
            propagated.append(mod_field)
        else:
            propagated.append(field)

    # Check we found the 'decode_f' field
    if inst.decode_f and not found_dc_f:
        raise ElaborationError(
            report.error(
                f"Could not resolve decode_f '{inst.decode_f}' for !Inst '{inst.name}'",
                item=inst
            ),
            ph_doc=inst
        )

    # Add in the fields unique to this instruction
    propagated += inst.fields

    return ("_".join([basename, name]) if basename else name, basename, propagated)

def elaborate_instruction(top, scope, max_depth):
    """ Evaluate a !Inst and generate a DFCommand.

    Args:
        top      : The top-level !Inst to elaborate from
        scope    : An ElaboratorScope object containing all documents included
                 : directly or indirectly by the top module.
        max_depth: The maximum depth to elaborate to (optional, not used)

    Returns:
        DFCommand: DesignFormat command representing the instruction
    """
    # Sanity check
    assert isinstance(top, Inst)

    # Build the full list of fields for this instruction
    (name, basename, fields) = resolve_instruction(top, scope)

    # Build a DFCommand
    df_inst = DFCommand(
        id          = top.name,
        width       = 32,
        description = top.ld if top.ld else top.sd,
    )

    # Append options
    options_to_attributes(top, df_inst)

    # If we are inheriting, list the base instruction
    if top.base:
        df_inst.setAttribute('base',     top.base)
        df_inst.setAttribute('fullbase', basename)
    if top.decode_f:
        df_inst.setAttribute('decode_f', top.decode_f)
    if top.decode_f:
        df_inst.setAttribute('decode_e', top.decode_e)

    # For every field in the instruction
    for field in fields:
        xfield = { "ref_cb": resolve_xref, "ref_ctx": {"inst": top, "field": field} }

        # Get the requested LSB, MSB, and width of the field
        req_lsb = scope.evaluate_expression(field.lsb, **xfield) if field.lsb != None else None
        req_msb = scope.evaluate_expression(field.msb, **xfield) if field.msb != None else None

        # Establish the width and LSB of the field
        width = scope.evaluate_expression(field.width, **xfield) if field.width != None else 1
        reset = scope.evaluate_expression(field.reset, **xfield) if field.reset != None else 0
        lsb   = req_lsb if req_lsb != None else 0

        # Check LSB & MSB are compatible (if both specified)
        if req_lsb != None and req_msb != None:
            if (req_msb - width + 1) != req_lsb:
                raise ElaborationError(
                    report.error(
                        f"!Inst {top.name}.{field.name} LSB {req_lsb} and MSB "
                        f"{req_msb} don't agree",
                        item=field
                    ),
                    ph_doc=field
                )
        elif req_msb != None:
            lsb = (req_msb - width + 1)

        # Check if MSB goes beyond length of the instruction
        if (lsb + width - 1) > df_inst.width:
            raise ElaborationError(
                report.error(
                    f"!Inst {top.name}.{field.name} MSB {(lsb + width - 1)} is "
                    f"greater than the instruction width ({df_inst.width})",
                    item=field
                ),
                ph_doc=field
            )

        # NOTE: We don't check for overlaps, because !Inst fields may deliberately
        #       overlap for instructions with multiple parameter options.

        # Build the field
        df_field = DFCommandField(
            id = field.name, lsb = lsb, size = width, reset = reset,
            signed = False,
            description = (field.ld if field.ld != None else field.sd),
        )

        # Mark if this field is inherited from another instruction
        df_field.setAttribute('inherited', (field not in top.fields))

        # Append enumeration
        enum_val = -1
        for enum in field.enums:
            enum_val += 1 # Automatic enumeration
            if isinstance(enum.val, str) and len(enum.val.strip()) > 0:
                enum_val = scope.evaluate_expression(enum.val, **xfield)
            elif type(enum.val) in [int, bool, float]:
                enum_val = enum.val
            df_field.addEnumValue(enum.name, enum_val, enum.ld if enum.ld else enum.sd)

        # Append options
        options_to_attributes(field, df_field)

        # Append field to the !Inst
        df_inst.addField(df_field)

    return df_inst
