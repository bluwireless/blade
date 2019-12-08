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
report = reporting.get_report("elaborator.module")

# Import other elaborators that we need
from .address_map import elaborate_map
from .common import ElaborationError, options_to_attributes, tag_source_info
from .common import map_ph_to_df_role
from .registers import elaborate_registers
from .interconnect import build_interconnect

# Import schema types that we need
from ..schema import Point, Const, His, HisRef, Port, Mod, Config, Group, Register
from ..schema.ph_tag_base import CONSTANTS as PHConstants
from ..schema.schema_helpers import convert_to_class

# Import DesignFormat types that we need
from designformat import DFConstants, DFProject, DFBlock, DFPort, DFConstantTie
from designformat import DFInterconnect, DFInterconnectComponent

def resolve_mod_inheritance(mod, scope):
    """
    To support features such the automatic decoder flow, a !Mod must be able to
    extend from other !Mod definitions - carrying forward options, children,
    ports, and connectivity. This can happen recursively. This function returns
    a merged !Mod, taking into account the inheritance.

    Args:
        mod  : The !Mod to resolve
        scope: The Phhidle document scope to use for resolving !Mod

    Returns:
        Mod: The resolved !Mod with inherited properties
    """
    # If we don't extend, nothing to resolve!
    if mod.extends == None:
        return mod

    # Resolve the baseline, accomodating for recursive inheritance
    base = resolve_mod_inheritance(scope.get_document(mod.extends, Mod), scope)

    # Copy the passed module, use a shallow copy
    merged = copy(mod)

    # Update the copied baseline with attributes of this module
    # - Merge in any ports from the baseline that don't clash
    port_names    = [x.name for x in mod.ports]
    merged.ports += [x for x in base.ports if x.name not in port_names]

    # - Merge simple options from the baseline and make unique
    merged.options = list(set(mod.options + [x for x in base.options if not '=' in x]))

    # - Valued options, only merge in those from the baseline that don't clash
    valued_opts = [x.split('=')[0].strip() for x in merged.options if '=' in x]
    for opt in (x for x in base.options if '=' in x):
        if not opt.split('=')[0].strip() in valued_opts:
            merged.options.append(opt)

    # - Choose the base's short description if module doesn't provide one
    merged.sd = base.sd if merged.sd == None else merged.sd

    # - Merge any child modules that don't clash
    child_names     = [x.name for x in mod.modules]
    merged.modules += [x for x in base.modules if x.name not in child_names]

    # - Merge explicit connections
    # TODO: Need to be smarter about this merge and check for eliminated ports
    merged.connections += base.connections

    # - Choose the base's long description if module doesn't provide one
    merged.ld = base.ld if merged.ld == None else merged.ld

    # - Merge in defaults
    # NOTE: A default can be overridden by an explicit connection as they are
    #       resolved first!
    merged.defaults += base.defaults

    # - Merge other attributes
    if base.requirements:
        merged.requirements  = merged.requirements if merged.requirements != None else []
        merged.requirements += base.requirements

    if base.importhisrefs:
        merged.importhisrefs  = merged.importhisrefs if merged.importhisrefs != None else []
        merged.importhisrefs += base.importhisrefs

    merged.clk_root = merged.clk_root if merged.clk_root != None else base.clk_root
    merged.rst_root = merged.rst_root if merged.rst_root != None else base.rst_root

    # Return the merge result
    return merged

def resolve_point_to_ports(block, xmap, point):
    """
    Resolve the !Point connection to a list of ports (it can be multiple ports
    as module instantiation can have a count > 1)

    Args:
        block: The parent block to resolve within
        xmap : The expansion map of child modules
        point: The !Point instance to resolve

    Returns:
        list: List of !DFPorts expanded from the provided !Point
    """
    if not point.mod or len(point.mod.strip()) == 0:
        port = block.resolvePath(f"[{point.port}]");
        if not port:
            raise ElaborationError(report.error(f"Could not find port {point.port} on block {block.id}"))
        return [port]
    else:
        mods  = xmap[point.mod] if point.mod in xmap else [point.mod]
        ports = []
        for mod_name in mods:
            port = block.resolvePath(f"{mod_name}[{point.port}]")
            if not port:
                raise ElaborationError(report.error(f"Could not find port {point.port} on block {mod_name}"))
            ports.append(port)
        return ports

def list_unconnected_ports(block, xmap, defaults):
    """ Search through the parent and child blocks for all unconnected ports

    Args:
        block   : The block to search through
        xmap    : The expansion map of child modules
        defaults: A list of Phhidle !Points that tie signals off

    Returns:
        namespace: Returns namespace of all unconnected parent and child ports
    """
    # Take copies of the arrays so that we can delete as required
    top_in  = block.ports.input[:]
    top_out = block.ports.output[:]
    top_bi  = block.ports.inout[:]

    # Identify all ports on parent and children that are tied off in 'defaults'
    defaulted_ports = []
    for point in (defaults if isinstance(defaults, list) else []):
        defaulted_ports += resolve_point_to_ports(block, xmap, point)

    # Eliminate all ports on the master that have been listed in 'defaults'
    for port in defaulted_ports:
        if port in top_in:
            top_in.remove(port)
        elif port in top_out:
            top_out.remove(port)
        elif port in top_bi:
            top_bi.remove(port)

    # Eliminate already connected ports on the parent
    for conn in block.connections:
        # Inbound connection matches
        if conn.start_port.block == block and conn.start_port in top_in:
            top_in.remove(conn.start_port)
        # Outbound connection matches
        if conn.end_port.block == block and conn.end_port in top_out:
            top_out.remove(conn.end_port)
        # Bidirectional connection matches (we treat as inbound)
        if conn.start_port.block == block and conn.start_port in top_bi:
            top_bi.remove(conn.start_port)

    # Build a full list of unconnected child ports
    child_ports = {}

    for child in block.children:
        child_in  = child.ports.input[:]
        child_out = child.ports.output[:]
        child_bi  = child.ports.inout[:]

        # Eliminate any ports tied-off by defaults
        for port in defaulted_ports:
            if port in child_in:
                child_in.remove(port)
            elif port in child_out:
                child_out.remove(port)
            elif port in child_bi:
                child_bi.remove(port)

        # Eliminate already connected ports on the child
        for conn in block.connections:
            # Outbound connection matches
            if conn.start_port.block == child and conn.start_port in child_out:
                child_out.remove(conn.start_port)
            # Inbound connection matches
            if conn.end_port.block == child and conn.end_port in child_in:
                child_in.remove(conn.end_port)
            # Bidirectional connection matches (we treat as inbound)
            if conn.end_port.block == child and conn.end_port in child_bi:
                child_bi.remove(conn.end_port)

        # Only include this child if we have any ports
        if len(child_in + child_out + child_bi) > 0:
            child_ports[child.id] = {
                'in_ports'   : child_in,
                'out_ports'  : child_out,
                'inout_ports': child_bi
            }

    return convert_to_class({
        'parent'  : { 'in_ports': top_in, 'out_ports': top_out, 'inout_ports': top_bi, },
        'children': child_ports
    })

def elaborate_p2c_connections(block, p_in, c_ports, relaxed=False, bidir=False):
    """ Elaborate all implict connections passing from the parent block to a child.

    Args:
        block  : The block we are working within
        p_in   : The parent's unconnected inbound port set
        c_ports: The unconnected child port set
        relaxed: Use relaxed matching where only type examined (default: False)
        bidir  : Handling bidirectional ports (default: False)
    """
    for top_in in p_in:
        for key in c_ports.keys():
            for child_in in (c_ports[key].inout_ports if bidir else c_ports[key].in_ports):
                if (
                    (child_in.type == top_in.type) and
                    (relaxed or (child_in.name == top_in.name))
                ):
                    report.debug(f"    + Connecting {top_in.id} -> {child_in.id}")
                    # Ports can carry multiple signals, find the lowest common number
                    common_count = min(top_in.count, child_in.count)
                    top_size     = len(top_in.getOutboundConnections())
                    child_size   = len(child_in.getInboundConnections())
                    for i in range(common_count):
                        top_i   = (i + top_size  ) % top_in.count
                        child_i = (i + child_size)
                        if child_i >= child_in.count:
                            report.warning(f"Multiple candidates for automatic connection to port {child_in.id} in block {block.id}")
                            break
                        block.addConnection(top_in, top_i, child_in, child_i)

def elaborate_c2p_connections(block, p_out, c_ports, relaxed=False):
    """ Elaborate all implicit connections passing from a child block to the parent.

    Args:
        block  : The block we are working within
        p_out  : The parent's unconnected outbound port set
        c_ports: The unconnected child port set
        relaxed: Use relaxed matching where only type examined (default: False)
    """
    for top_out in p_out:
        for key in c_ports.keys():
            for child_out in c_ports[key].out_ports:
                if (
                    (child_out.type == top_out.type) and
                    (relaxed or (child_out.name == top_out.name))
                ):
                    report.debug(f"    + Connecting {child_out.id} -> {top_out.id}")
                    # Ports can carry multiple signals, find the lowest common number
                    common_count = min(top_out.count, child_out.count)
                    child_size   = len(child_out.getOutboundConnections())
                    top_size     = len(top_out.getInboundConnections())
                    for i in range(common_count):
                        child_i = (i + child_size) % child_out.count
                        top_i   = (i + top_size  )
                        if top_i >= top_out.count:
                            report.warning(f"Multiple candidates for automatic connection to port {top_out.id} in block {block.id}")
                            break
                        block.addConnection(child_out, child_i, top_out, top_i)

def elaborate_c2c_connections(block, c_ports, relaxed=False):
    """ Elaborate all implicit connections passing between child blocks.

    Args:
        block   The block we are working within
        c_ports The unconnected child port set
        relaxed Use relaxed matching where only type examined (default: False)
    """
    for key_a in c_ports.keys():
        for key_b in c_ports.keys():
            # Avoid building loop back connections
            if key_a == key_b:
                continue

            # Perform pairings
            for src in c_ports[key_a].out_ports:
                for tgt in c_ports[key_b].in_ports:
                    if (
                        (src.type == tgt.type) and
                        (relaxed or (src.name == tgt.name))
                    ):
                        report.debug(f"    + Connecting {src.id} -> {tgt.id}")
                        # Ports can carry multiple signals, find the lowest common number
                        common_count = min(src.count, tgt.count)
                        src_size     = len(src.getOutboundConnections())
                        tgt_size     = len(tgt.getInboundConnections())
                        for i in range(common_count):
                            src_i = (i + src_size) % src.count
                            tgt_i = (i + tgt_size)
                            if tgt_i >= tgt.count:
                                report.warning(f"Multiple candidates for automatic connection to port {tgt.id} in block {block.id}")
                                break
                            block.addConnection(src, src_i, tgt, tgt_i)

def build_tree(module, instance_name, parent, scope, max_depth=None, depth=0):
    """
    Recursively convert the Phhidle document definition of the design into a
    DesignFormat hierarchy.

    Args:
        module       : The definition of this block
        instance_name: The name of this instantiation
        parent       : The parent block (as a DFBlock)
        scope        : The Phhidle document scope for resolution
        max_depth    : The maximum depth to elaborate to
        depth        : The current depth we are working at

    Returns:
        DFBlock: The elaborated block complete with ports, children, etc.
    """
    # ==========================================================================
    # Stage 1: Build the block
    # ==========================================================================
    report.debug(f"Elaborating {module.name}")

    # If the !Mod specifies an 'extends' attribute, we need to resolve it
    if module.extends != None:
        module = resolve_mod_inheritance(module, scope)

    # Build the block based on the resolved module
    block = DFBlock(
        instance_name,
        module.name,
        parent,
        module.ld if module.ld != None else module.sd
    )

    # Attach any attributes
    options_to_attributes(module, block)

    # Mark if this block is a leaf node
    # NOTE: We can rely on this attribute even in a shallow elaboration
    block.setAttribute(DFConstants.ATTRIBUTES.LEAF_NODE, (len(module.modules) == 0))

    # Tag where this object came from
    tag_source_info(module, block)

    # Attach any referenced His under 'importhisrefs'
    # NOTE: This is to support the mod_import flow - potentially this should be
    #       eliminated over time by using RTL wrappers instead.
    if module.importhisrefs:
        imported_his = []
        for his_ref in module.importhisrefs:
            imported_his.append(
                build_interconnect(scope.get_document(his_ref.ref, His), scope)
            )
        block.setAttribute('importedhisrefs', imported_his)

    # ==========================================================================
    # Stage 2: Attach input and output ports
    # ==========================================================================
    if module.ports:
        report.debug(f"Expanding ports of: {module.name}")
        for port in module.ports:
            # Determine the direction of the port
            direction = {
                PHConstants.ROLES.SLAVE : DFConstants.DIRECTION.INPUT,
                PHConstants.ROLES.MASTER: DFConstants.DIRECTION.OUTPUT,
                PHConstants.ROLES.BI    : DFConstants.DIRECTION.INOUT,
            }[port.role]

            # Calculate port count, if not defined assume it's 1
            port_count = 1
            if port.count:
                port_count = int(scope.evaluate_expression(port.count))

            # If the port count is evaluated to zero, don't construct it
            if port_count == 0:
                report.debug(
                    f"Skipping {direction} port {port.name} of type {port.ref} "
                    "as the count evaluated to zero"
                )
                continue

            # Construct a new port object
            report.debug(
                f"Building {direction} port {port.name} of type {port.ref} "
                f"with count {port_count}"
            )
            new_port = DFPort(
                port.name, port.ref, port_count, direction, block,
                (port.ld if port.ld else port.sd)
            )

            # Attach attributes
            options_to_attributes(port, new_port)

            # Attach the port to the block
            block.addPort(new_port)
        report.debug(f"Finished expanding ports of: {module.name}")

    # ==========================================================================
    # Stage 3: Create automatic clock and reset signals
    # ==========================================================================
    main_clock = None
    main_reset = None

    if not block.getAttribute('NO_AUTO_CLK_RST') and not block.getAttribute('NO_CLK_RST'):
        if not main_clock:
            main_clock = DFPort('clk', 'clock', 1, DFConstants.DIRECTION.INPUT, block)
            main_clock.setAttribute('AUTO_CLK', True)
            main_clock.setAttribute('EXPLICIT_NAME', True)
            block.addPort(main_clock)
        if not main_reset:
            main_reset = DFPort('rst', 'reset', 1, DFConstants.DIRECTION.INPUT, block)
            main_reset.setAttribute('AUTO_RST', True)
            main_reset.setAttribute('EXPLICIT_NAME', True)
            block.addPort(main_reset)

    # ==========================================================================
    # Stage 4: Identify principal clock and reset signals
    # ==========================================================================

    # If missing, try picking the explicit clock & reset
    if not main_clock or not main_reset:
        for port in block.ports.input:
            if not main_clock and port.getAttribute('AUTO_CLK'):
                main_clock = port
            elif not main_reset and port.getAttribute('AUTO_RST'):
                main_reset = port

    # Make sure that the main clock and reset are nominated as principal signals
    if main_clock:
        report.debug(f"Identified main clock signal: {main_clock.id}")
        block.setPrincipalSignal(main_clock)
    if main_reset:
        report.debug(f"Identified main reset signal: {main_reset.id}")
        block.setPrincipalSignal(main_reset)

    # If the depth of the elaboration is constrained, check if we should break
    if max_depth != None and depth >= max_depth:
        return block

    # ==========================================================================
    # Stage 5: Expand all child modules
    # ==========================================================================
    child_keys    = []
    expansion_map = {}

    if module.modules:
        report.debug(f"Expanding children of: {module.name}")
        for item in module.modules:
            report.debug(f"Building child {item.name} of type {item.ref}")
            # Locate the definition of this module
            mod_ref = scope.get_document(item.ref, Mod)
            if not mod_ref:
                raise ElaborationError(report.error(f"Could not resolve child {item.name}"))
            # Evaluate the number of instances of this module
            count   = scope.evaluate_expression(item.count) if item.count else 1
            # Build the child instance
            expands_to = []
            for i in range(count):
                instance_name = f"{item.name}_{i}"
                sub_block     = build_tree(
                    mod_ref, instance_name, block, scope, max_depth, (depth+1)
                )
                if item.ld or item.sd:
                    sub_block.description = item.ld if item.ld else item.sd
                block.addChild(sub_block)
                expands_to.append(instance_name)
            # Keep track of expansions
            expansion_map[item.name] = expands_to
        report.debug(f"Finished expanding children of: {module.name}")

    # Pickup 'clk_root' and 'rst_root' nominated signals
    if module.clk_root and isinstance(module.clk_root, Point):
        main_clock = resolve_point_to_ports(block, expansion_map, module.clk_root)[0]
        report.debug(f"Identified root clock signal: {main_clock.id}")
        block.setPrincipalSignal(main_clock)

    if module.rst_root and isinstance(module.rst_root, Point):
        main_reset = resolve_point_to_ports(block, expansion_map, module.rst_root)[0]
        report.debug(f"Identified root reset signal: {main_reset.id}")
        block.setPrincipalSignal(main_reset)

    # ==========================================================================
    # Stage 6: Expand Explicit Connections
    # ==========================================================================

    # Keep track of which signals within each port have been connected already
    # NOTE: Ports can carry a signal count > 1
    sig_idxs = {}
    def get_signal_index(port):
        port_id = port.hierarchicalPath()
        index   = sig_idxs[port_id] if port_id in sig_idxs else 0
        # Wrap to allow multiple connections
        if index >= port.count:
            index = 0
        # Keep track of the last connected index
        sig_idxs[port_id] = (index + 1)
        return index

    # Expand every explicit connection (including fan-ins and fan-outs)
    report.debug(f"Expanding explicit connections of: {module.name}")
    for conn in (module.connections if module.connections else []):
        # ----------------------------------------------------------------------
        # Resolve point->point connections
        # ----------------------------------------------------------------------
        if conn.points and len(conn.points) > 0:
            sources = []
            targets = []

            # Run through the points categorising each as source or target
            for point in conn.points:
                ports = resolve_point_to_ports(block, expansion_map, point)
                for port in ports:
                    # If the port is on the current block - an INPUT becomes a
                    # SOURCE, whilst an OUTPUT becomes a TARGET
                    if port.block == block:
                        if port.direction == DFConstants.DIRECTION.INPUT:
                            sources.append(port)
                        else:
                            targets.append(port)
                    # If the port is on a child block - an INPUT is a target, and
                    # an OUTPUT is a SOURCE
                    else:
                        if port.direction == DFConstants.DIRECTION.INPUT:
                            targets.append(port)
                        else:
                            sources.append(port)

            # Build one->one connections
            if len(sources) == len(targets):
                for i in range(len(sources)):
                    report.debug(f"Building one->one connection {sources[i].id} -> {targets[i].id}")
                    for j in range(targets[i].count):
                        block.addConnection(
                            sources[i], get_signal_index(sources[i]),
                            targets[i], get_signal_index(targets[i])
                        )
            # Build one->many connections
            elif len(sources) == 1 and len(targets) > 1:
                for i in range(len(targets)):
                    report.debug(f"Building one->many connection {sources[0].id} -> {targets[i].id}")
                    for j in range(targets[i].count):
                        # If source count is zero, this is a fan-out of a single signal
                        src_index = get_signal_index(sources[0]) if sources[0].count > 1 else 0
                        block.addConnection(
                            sources[0], src_index,
                            targets[i], get_signal_index(targets[i])
                        )
            # Build many->one connections
            elif len(sources) > 1 and len(targets) == 1:
                for i in range(len(sources)):
                    report.debug(f"Building many->one connection {sources[i].id} -> {targets[0].id}")
                    for j in range(sources[i].count):
                        block.addConnection(
                            sources[i], get_signal_index(sources[i]),
                            targets[0], get_signal_index(targets[0])
                        )
            # Otherwise this is a bad connection
            else:
                raise ElaborationError(report.error(
                    f"Bad connection {len(sources)} sources => {len(targets)} targets"
                ))

        # ----------------------------------------------------------------------
        # Resolve point->constant connections
        # ----------------------------------------------------------------------
        if conn.constants and len(conn.constants) > 0:
            constant   = None
            tied_ports = []
            for point in conn.constants:
                if isinstance(point, Const):
                    if constant != None:
                        raise ElaborationError(report.error(f"Multiple constants for single connection"))
                    constant = point
                elif isinstance(point, Point):
                    tied_ports += resolve_point_to_ports(block, expansion_map, point)
                else:
                    raise ElaborationError(report.error(f"Unknown connection point type {type(point)}"))

            if not constant:
                raise ElaborationError(report.error("Could not find a constant in the connection"))

            for port in tied_ports:
                tie = DFConstantTie(
                    scope.evaluate_expression(constant.value), False, block
                )
                report.debug(f"Tying port {port.id} to constant {tie.id}")
                # Need to work out which signal index is being tied-off
                tie_index = len([x for x in port.connections if x.end_port == port])
                block.addTieOff(port, tie_index, tie)

    report.debug(f"Finished expanding explicit connections of: {module.name}")

    # ==========================================================================
    # Stage 7: Implicit clock and reset signal distribution
    # ==========================================================================

    report.debug(f"Distributing clock and reset signals of: {module.name}")

    # Get the list of ports that have been tied off in the 'defaults' section
    defaults = []
    for point in (module.defaults if isinstance(module.defaults, list) else []):
        defaults += resolve_point_to_ports(block, expansion_map, point)

    for child in block.children:
        child_clock = child.getPrincipalSignal('clock')
        child_reset = child.getPrincipalSignal('reset')
        # Distribute the main clock signal
        # NOTE: The child may nominate a 'clk_root', which may not be a port on
        #       the block - so if it's not an input port, ignore it
        if main_clock and child_clock and child_clock in child.ports.input:
            # If no existing connections and not default tied, link the clock
            if len(child_clock.getInboundConnections()) == 0 and not child_clock in defaults:
                report.debug(f"Connecting clock from {main_clock.id} to {child_clock.id}")
                block.addConnection(main_clock, 0, child_clock, 0)
        # Distribute the main reset signal
        # NOTE: Same applies for a nominated 'rst_root'
        if main_reset and child_reset and child_reset in child.ports.input:
            # If no existing connections and not default tied, link the reset
            if len(child_reset.getInboundConnections()) == 0 and not child_reset in defaults:
                report.debug(f"Connecting reset from {main_reset.id} to {child_reset.id}")
                block.addConnection(main_reset, 0, child_reset, 0)

    report.debug(f"Finished distributing clock and reset signals of: {module.name}")

    # ==========================================================================
    # Stage 8: Implicit connections - run twice, first strict then relaxed
    # ==========================================================================

    report.debug(f"Building implicit connections of: {module.name}")

    # NOTE: 'strict' elaboration requires both name and type to match, 'relaxed'
    #       elaboration requires only type to match. Lower chance of error if we
    #       run strict followed by relaxed.

    for i in range(2):
        # Build a full listing of the unconnected top-level ports
        report.debug(f"Listing unconnected ports")
        unconn = list_unconnected_ports(block, expansion_map, module.defaults)

        # Elaborate implicit parent->child inbound connections
        report.debug(f"Elaborating parent->child inbound connections")
        elaborate_p2c_connections(block, unconn.parent.in_ports, unconn.children, (i==1))

        # Elaborate implicit parent->child bidirectional connections (treat as inbound)
        report.debug(f"Elaborating parent->child bidirectional connections")
        elaborate_p2c_connections(block, unconn.parent.inout_ports, unconn.children, (i==1), bidir=True)

        # Elaborate implicit child->parent outbound connections
        report.debug(f"Elaborating child->parent outbound connections")
        elaborate_c2p_connections(block, unconn.parent.out_ports, unconn.children, (i==1))

        # Elaborate implicit child->child interconnections
        report.debug(f"Elaborating child->child interconnections")
        elaborate_c2c_connections(block, unconn.children, (i==1))

    report.debug(f"Finished building implicit connections of: {module.name}")

    # ==========================================================================
    # Stage 9: Attach an included register definition to the block
    # ==========================================================================

    # Detect if a register set was directly included
    config_tag = None
    for file in module.source.all_included_files():
        all_docs = file.get_parsed_documents()
        # Detect a defined !Config tag
        if Config in (type(x) for x in all_docs):
            config_tag = [x for x in all_docs if isinstance(x, Config)][0]
            break
        # Construct a !Config tag with the groups listed in order discovered
        elif Group in (type(x) for x in all_docs):
            config_tag = Config([Register(x.name) for x in all_docs if isinstance(x, Group)])
            break

    # If a !Config tag has been picked up (or constructed), build the registers
    if config_tag:
        for reg_group in elaborate_registers(config_tag, scope):
            block.addRegister(reg_group)

    # ==========================================================================
    # Stage 10: Check for any remaining unconnected ports and warn about them
    # ==========================================================================
    unconn = list_unconnected_ports(block, expansion_map, module.defaults)

    all_ports = []

    # NOTE: If this block has implementation, ports may appear not to be connected
    # NOTE: DECODER attribute signifies a block using the legacy Reg decoder flow (effectively an IMP)
    if config_tag == None and not block.getAttribute('IMP') and not block.getAttribute('DECODER'):
        all_ports += unconn['parent']['in_ports']
        all_ports += unconn['parent']['out_ports']
        all_ports += unconn['parent']['inout_ports']

    # Children should always be full connected
    for child in unconn['children'].values():
        all_ports += child['in_ports']
        all_ports += child['out_ports']
        all_ports += child['inout_ports']

    # Loop through all of the unconnected ports and list what is still disconnected
    for port in all_ports:
        report.warning(f"Port unconnected after elaboration: {port.block.hierarchicalPath()}[{port.name}]", item=port)

    # ==========================================================================
    # Stage 11: Expand an address map if present
    # ==========================================================================

    # Detect if an address map was defined
    if module.addressmap and len(module.addressmap) > 0:
        elaborate_map(module.addressmap, block, scope)

    # Return this block
    return block

def elaborate_module(top, scope, max_depth=None):
    """
    Elaborate a !Mod tag instance, expanding hierarchy and resolving connections
    up to the maximum requested depth.

    Args:
        top      : The top-level !Mod to elaborate from
        scope    : An ElaboratorScope object containing all documents included
                   directly or indirectly by the top module.
        max_depth: The maximum depth to elaborate to (optional, by default
                   performs a full depth elaboration - max_depth=None)

    Returns:
        DFProject: Contains the elaborated block and all interconnects used
    """
    # Build a new project
    project = DFProject(top.name, top.source.path)

    # Build the tree for the root block
    block = build_tree(
        top,                    # The top-level !Mod to evaluate
        top.name,               # Name to use for the top-level !Mod instance
        None,                   # No parent exists
        scope,                  # Scope to use for elaboration
        max_depth = max_depth   # Maximum depth to elaborate to
    )

    # Attach the block as a principal node to the project
    project.addPrincipalNode(block)

    # Get a list of all of the interconnection types directly used by the design
    def list_interconnects(block):
        types = [x.type for x in block.getAllPorts()]
        for child in block.children:
            types += list_interconnects(child)
        return types

    used_types = []

    for block in (x for x in project.nodes.values() if isinstance(x, DFBlock)):
        used_types += list_interconnects(block)

    # Expand the directly used types to include all referenced types
    def chase_his(his_ref):
        his = scope.get_document(his_ref, His)
        if not his:
            raise ElaborationError(report.error(f"Could not locate His {his_ref}"))
        sub_his  = [x for x in his.ports if isinstance(x, HisRef)]
        required = [his] + [scope.get_document(x.ref, His) for x in sub_his]
        for item in sub_his:
            required += chase_his(item.ref)
        return required

    all_required = []
    for his_type in used_types:
        all_required += chase_his(his_type)

    # Ensure the list of His types is unique
    all_required = list(set(all_required))

    # Build and attach descriptions of each interconnect type
    for his in all_required:
        project.addReferenceNode(build_interconnect(his, scope))

    # Log all of the interconnect types that were detected
    report.info(
        f"Identified {len(all_required)} interconnect types in the design",
        body="\n".join((x.name for x in all_required))
    )

    # Log the design hierarchy
    def chase_hierarchy(block, depth=0):
        intro = ""
        if depth > 0: intro += (" | " * (depth - 1)) + " |-"
        intro += block.id
        lines = [intro]
        for child in block.children: lines += chase_hierarchy(child, depth+1)
        return lines

    txt_hier = chase_hierarchy(block)
    report.info(
        f"Design hierarchy contains {len(txt_hier)} nodes", body="\n".join(txt_hier)
    )

    # Return the project
    return project
