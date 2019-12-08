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

from math import ceil

# Get hold of the report
from .. import reporting
report = reporting.get_report("checker.apertures")

# Import the rule violation custom exception type
from .common import RuleViolation, CriticalRuleViolation

# Import DesignFormat project
from designformat import DFProject, DFBlock, DFRegister, DFRegisterGroup, DFPort

def chase_driver(port: DFPort, index: int):
    """ Chase the connections to a port back to the original driver

    Args:
        port: The DFPort instance to start chasing from

    Returns:
        DFPort: Original driving DFPort instance
    """
    inbound = port.getInboundConnections()
    # If no inbound connections, then this must be the driver
    if len(inbound) == 0: return (port, index)

    # Otherwise, identify connections for the correct index
    filtered = [x for x in inbound if x.end_port == port and x.end_index == index]
    if len(filtered) == 0: return (port, index)
    elif len(filtered) > 1:
        raise CriticalRuleViolation(
            f"Detected diverging connection tree for {port.hierarchicalPath()} "
            f"- ports cannot have more than one driver!",
            node=port
        )

    # Chase to the driver of this port
    return chase_driver(filtered[0].start_port, filtered[0].start_index)

def check_apertures(project: DFProject):
    """ Check that register maps of blocks are visible through the aperture

    Args:
        project: Project to check through

    Returns:
        list: List of any RuleViolations that have been detected
    """

    # Create storage for any detected violations
    violations = []

    # Check if the principal node is a DFBlock
    if len(project.getAllPrincipalNodes()) == 0:
        report.debug("Project contains no principal nodes - skipping check")
        return violations

    roots = [x for x in project.getAllPrincipalNodes() if type(x) == DFBlock]
    if len(roots) == 0:
        report.debug("Project contains no DFBlock principal nodes - skipping check")
        return violations

    # For each root node, search out every DFBlock with attached registers
    def find_reg_blocks(block):
        found = []
        # First iterate through any child blocks
        for child in block.children:
            found += find_reg_blocks(child)
        # Check if I have registers?
        if len(block.registers) != 0:
            found.append(block)
        return found

    reg_blocks = []
    for block in roots:
        reg_blocks += find_reg_blocks(block)

    report.info(
        f"Found the following {len(reg_blocks)} register blocks",
        body="\n".join([" - " + x.hierarchicalPath() for x in reg_blocks])
    )

    # If we didn't find any register blocks, skip the check
    if len(reg_blocks) == 0:
        report.debug("Project contains no register blocks - skipping check")
        return violations

    # Iterate through every located block with registers
    curr_violations = 0
    for block in reg_blocks:
        report.debug(f"Examining block: {block.hierarchicalPath()}")

        # Keep track of how many violations have already been recorded
        curr_violations = len(violations)

        # First, try to locate which port is attached to an address map
        access_port = None
        for port in block.ports.input:
            for port_idx in range(port.count):
                # Find out who drives this port
                # NOTE: This is tuple of a DFPort and the port index (integer)
                driver = chase_driver(port, port_idx)
                # Does the driver has an address map that we can chase through?
                if not driver[0].block.address_map: continue
                # Is there a target on the address map for the driver port?
                if not driver[0].block.address_map.getTarget(driver[0], driver[1]): continue
                # We found our access point!
                access_port = (port, port_idx)
                break

        # If we didn't find an access port, this is a violation
        if access_port == None:
            violations.append(RuleViolation(
                f"Could not establish access port for block {block.hierarchicalPath()}",
                block
            ))
            continue

        # Now we want to find all address maps in a direct chain
        address_maps = []
        def find_maps(port, port_idx):
            # Get the first address map in the chain
            driver = chase_driver(port, port_idx)
            addr   = driver[0].block.address_map
            if not addr: return
            address_maps.append({ "map": addr, "port": driver[0], "index": driver[1] })
            # Identify the target port for the driver
            tgt = addr.getTarget(driver[0], driver[1])
            if not tgt: return
            # How many initiators can access this target?
            inits = addr.getInitiatorsForTarget(tgt)
            if len(inits) == 0:
                violations.append(RuleViolation(
                    f"No initiators can access port '{driver[0].name}' in address "
                    f"map of '{driver[0].block.hierarchicalPath()}'",
                    node=driver
                ))
                return
            # If we have more than one initiator, the path has diverged - so stop
            if len(inits) > 1: return
            # So if we have exactly one initiator, chase it
            return find_maps(inits[0].port, inits[0].port_index)
        find_maps(*access_port)

        # Check no new violations have been raised
        if len(violations) > curr_violations: continue

        report.debug(
            f"Identified {len(address_maps)} address maps in driving chain for "
            f"port '{access_port[0].hierarchicalPath()}' index {access_port[1]}"
        )

        # Identify the highest address in the register map
        max_reg = None
        for reg in block.registers:
            if type(reg) == DFRegisterGroup:
                for grp_reg in reg.registers:
                    if type(grp_reg) != DFRegister:
                        raise CriticalRuleViolation(
                            f"Invalid node '{reg.id}' of type {type(reg).__name__} "
                            f"in register group",
                            reg
                        )
                    if not max_reg or grp_reg.getOffset() > max_reg.getOffset():
                        max_reg = grp_reg
            elif type(reg) == DFRegister:
                if not max_reg or reg.getOffset() > max_reg.getOffset():
                    max_reg = reg
            else:
                raise CriticalRuleViolation(
                    f"Invalid node '{reg.id}' of type {type(reg).__name__} in "
                    f"block's register set",
                    block
                )
        if max_reg == None:
            report.info(f"No registers found in {block.hierarchicalPath()}")
            return violations
        report.debug(
            f"Maximum register offset of {block.hierarchicalPath()} is "
            f"{hex(max_reg.getOffset())} with size {ceil(max_reg.width / 8)}"
        )
        max_address = max_reg.getOffset() + int(ceil(max_reg.width / 8))

        # Walk each address map checking that register block is accessible
        for addr in address_maps:
            tgt = addr['map'].getTarget(addr['port'], addr['index'])
            # Check maximum address is within the aperture size
            if max_address > tgt.aperture:
                violations.append(RuleViolation(
                    f"Register {block.hierarchicalPath()}.{max_reg.id} at offset "
                    f"{hex(max_reg.getOffset())} does not fit in the address map "
                    f"aperture of {tgt.aperture} bytes.\n"
                    f"Block        : {block.hierarchicalPath()}\n"
                    f"Register     : {max_reg.id} @ {hex(max_reg.getOffset())}\n"
                    f"Map          : {addr['map'].block.hierarchicalPath()}\n"
                    f"Target Offset: {hex(tgt.offset)}\n"
                    f"Aperture Size: {tgt.aperture}\n",
                    block
                ))
                break
            # Examine every initiator in this address map
            for init in addr['map'].initiators:
                tgt_inits = addr['map'].getInitiatorsForTarget(tgt)
                # If this initiator can't access the target, warn about it
                if init not in tgt_inits:
                    report.warning(
                        f"Restricted Access To {block.hierarchicalPath()}",
                        body=f"Register block {block.hierarchicalPath()} cannot "
                        f"be accessed from {init.port.hierarchicalPath()} "
                        f"index {init.port_index}"
                    )
                    continue
                # Check that the initiator's offset and mask are sufficient
                init_min = init.offset
                init_max = init.offset + init.mask + 1
                if tgt.offset < init_min or (tgt.offset + max_address) > init_max:
                    violations.append(RuleViolation(
                        f"Not all registers of {block.id} can be accessed by {init.port.id} "
                        f"index {init.port_index}:\n"
                        f"Block         : {block.hierarchicalPath()}\n"
                        f"Address Map   : {addr['map'].block.hierarchicalPath()}\n"
                        f"Target Port   : {tgt.port.id}\n"
                        f"Target Min    : {hex(tgt.offset)}\n"
                        f"Target Max    : {hex(tgt.offset + max_address)}\n"
                        f"Initiator Port: {init.port.id}\n"
                        f"Initiator Min : {hex(init_min)}\n"
                        f"Initiator Max : {hex(init_max)}\n",
                        block
                    ))
                    continue

        # Check we have no new violations
        if len(violations) > curr_violations: continue

    # Return the list of detected violations
    return violations
