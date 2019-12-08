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

# Get hold of the report
from .. import reporting
report = reporting.get_report("elaborator.interconnect")

from .common import ElaborationError, options_to_attributes, tag_source_info
from .common import map_ph_to_df_role

from ..schema import His, HisRef, Port
from ..schema.ph_tag_base import CONSTANTS as PHConstants
from designformat import DFInterconnect, DFInterconnectComponent, DFConstants
from designformat import DFProject

def build_interconnect(his, scope):
    """
    Evaluate a !His instance, resolving referred interconnect types and converting
    to a DFInterconnectType.

    Args:
        his  : The top-level !His to evaluate
        scope: An ElaboratorScope object containing all documents included
               directly or indirectly by the top module.
    """
    intc_role = map_ph_to_df_role(his.role)
    new_intc = DFInterconnect(his.name, intc_role, his.ld if his.ld else his.sd)

    # Attach interconnect components
    for port in his.ports:
        # Work out the components role, if interconnect is bidirectional then so
        # are all the child components (propagate)
        port_role = map_ph_to_df_role(port.role)
        if intc_role == DFConstants.ROLE.BIDIR:
            port_role = DFConstants.ROLE.BIDIR
        # Build a complex component if a HisRef is specified
        new_comp = None
        if isinstance(port, HisRef):
            new_comp = DFInterconnectComponent(
                port.name, port_role, port.ld if port.ld else port.sd,
                DFConstants.COMPONENT.COMPLEX, port.ref,
                int(scope.evaluate_expression(port.count))
            )
        # Build a simple component if a Port is specified
        elif isinstance(port, Port):
            default = None
            if port.enum != None and len(port.enum) > 0 and isinstance(port.default, str):
                found = [x for x in port.enum if x.name.strip() == port.default.strip()]
                if len(found) == 1:
                    default = scope.evaluate_expression(found[0].val)
            if default == None:
                default = scope.evaluate_expression(port.default)
            new_comp = DFInterconnectComponent(
                port.name, port_role, port.ld if port.ld else port.sd,
                DFConstants.COMPONENT.SIMPLE,
                scope.evaluate_expression(port.width),
                int(scope.evaluate_expression(port.count)),
                default
            )
            # Attach enumerated values
            if port.enum:
                enum_val = -1
                for enum in port.enum:
                    enum_val += 1 # Automatically enumerate
                    if isinstance(enum.val, str) and len(enum.val.strip()) > 0:
                        enum_val = scope.evaluate_expression(enum.val)
                    elif type(enum.val) in [int, bool, float]:
                        enum_val = enum.val
                    new_comp.addEnumValue(enum.name, enum_val, enum.ld if enum.ld else enum.sd)
        else:
            raise ElaborationError(report.error("Unknown interconnect component type"))
        # Attach any options declared on the port to the component
        options_to_attributes(port, new_comp)
        # Attach the component to the interconnect
        new_intc.addComponent(new_comp)

    # Attach any options
    options_to_attributes(his, new_intc)

    # Tag where this His came from
    tag_source_info(his, new_intc)

    # Store the list of included files as an attribute
    if isinstance(his.includes, list) and len(his.includes) > 0:
        new_intc.setAttribute('includes', his.includes)

    # Return the interconnect type
    return new_intc

def elaborate_interconnect(his, scope, max_depth=None, project=None):
    """
    Evaluate top-level !His and every interconnect type it references, returning
    a DFProject. The top-level !His will be a principal node, whilst referenced
    interconnects will be reference nodes.

    Args:
        his      : The top-level !His to evaluate
        scope    : The ElaboratorScope object containing all referenced documents
        max_depth: Ignored at present, provided for compatibility (optional)
        project  : Project to append to, else a new one is created (optional)

    Returns:
        DFProject: Project containing the elaborated interconnect
    """
    # Build the top level interconnect
    df_intc = build_interconnect(his, scope)

    # If no project, create one and add the interconnect as principal
    if not project:
        project = DFProject(his.name, his.source.path)
        project.addPrincipalNode(df_intc)
    else:
        project.addReferenceNode(df_intc)

    # For any referenced interconnect types, build those as reference nodes
    for component in df_intc.components:
        if component.type == DFConstants.COMPONENT.COMPLEX:
            ref_his = scope.get_document(component.ref, expected=His)
            if not ref_his:
                raise ElaborationError(report.error(f"Failed to resolve His {component.ref}"))
            elaborate_interconnect(ref_his, scope, project=project)

    # Return the project
    return project
