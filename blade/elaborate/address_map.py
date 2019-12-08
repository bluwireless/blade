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
report = reporting.get_report("elaborator.address_map")

# Import other elaborators that twe need
from .common import ElaborationError

# Import schema types that we need
from ..schema import Point, Initiator, Target

# Import DesignFormat types that we need
from designformat import DFConstants, DFBlock, DFPort
from designformat import DFAddressMapInitiator, DFAddressMapTarget, DFAddressMap

def elaborate_map(map, block, scope):
    """
    Elaborate the address map from !Initiator and !Target tags, it also requires
    a fully elaborated block to work from as it needs to associate with boundary
    ports on the block.

    Args:
        map  : The collection of !Initiator and !Target tags
        block: A DFBlock instance to associate with
        scope: The YAML document scope used for resolving constants
    """
    # Check that the block is a DFBlock
    if not isinstance(block, DFBlock):
        raise ElaborationError(
            report.error(f"Expected block of type DFBlock - got {type(block).__name__}"),
            ph_doc=block
        )

    # Check that the map only contains acceptable objects
    if len([x for x in map if type(x) not in [Initiator, Target]]) > 0:
        raise ElaborationError(report.error(
            f"Unsupported type detected in address map of {block.id} expects "
            f"!Initiator and !Target"
        ), ph_doc=block)

    # Check that all initiators and targets refer to known ports
    for node in map:
        # Check the port is supported
        if not node.port or len(node.port) != 1 or not isinstance(node.port[0], Point):
            raise ElaborationError(
                report.error(f"No port declared for {type(node).__name__} in block {block.id}"),
                ph_doc=node
            )
        # Try to find the port
        port = None
        try:
            port = block.resolvePath(f"[{node.port[0].port}]")
        except Exception:
            raise ElaborationError(
                report.error(f"Could not resolve port {node.port[0].port} on block {block.id}"),
                ph_doc=node
            )
        # Check for the requested index
        # NOTE: We are re-using the 'mod' on a point to specify port index
        index = int(scope.evaluate_expression(node.port[0].mod)) if node.port[0].mod else 0
        if index < 0 or index >= port.count:
            raise ElaborationError(
                report.error(f"Index {index} for port {port.name} out-of-range on block {block.id}"),
                ph_doc=node
            )
        # Store the port and port index into the node
        node.df_port       = port
        node.df_port_index = index
        # Check ports referenced by constraints exist
        node.df_constraints = []
        if node.constrain:
            for constraint in node.constrain:
                # Check the constraint is supported
                if not isinstance(constraint, Point):
                    raise ElaborationError(
                        report.error(f"Incorrect type used for constraint: {type(constraint).__name__}"),
                        ph_doc=constraint
                    )
                # Try to find the port
                port = None
                try:
                    port = block.resolvePath(f"[{constraint.port}]")
                except Exception:
                    raise ElaborationError(
                        report.error(f"Could not resolve port {constraint.port} on block {block.id}"),
                        ph_doc=constraint
                    )
                # Check for the requested index
                # NOTE: Again we are re-using the 'mod' to specify port index
                index = int(scope.evaluate_expression(constraint.mod)) if constraint.mod else 0
                # Store the constraint port and index
                node.df_constraints.append({ "port": port, "index": index })

    # Split the map into initiators and targets
    initiators = [x for x in map if isinstance(x, Initiator)]
    targets    = [x for x in map if isinstance(x, Target   )]

    # Check we have a viable address map
    if len(initiators) == 0:
        raise ElaborationError(report.error(
            "Cannot elaborate address map without at least one !Initiator for "
            f"block {block.id}"
        ), ph_doc=block)
    elif len(targets) == 0:
        raise ElaborationError(report.error(
            "Cannot elaborate address map without at least one !Target for "
            f"block {block.id}"
        ), ph_doc=block)

    # Construct a new address map object associated to the block
    df_map = DFAddressMap(block)

    # Add each target into the address map
    for target in targets:
        df_target = DFAddressMapTarget(
            target.df_port, target.df_port_index, target.offset, target.aperture
        )
        df_map.addTarget(df_target)
        # Store the created target
        target.df_target = df_target

    # Add each initiator into the address map
    for initiator in initiators:
        df_initiator = DFAddressMapInitiator(
            initiator.df_port, initiator.df_port_index, initiator.mask,
            initiator.offset
        )
        df_map.addInitiator(df_initiator)
        # Store the created initiator
        initiator.df_initiator = df_initiator

    # Add constraints specified on the initiators
    for initiator in initiators:
        for constraint in initiator.df_constraints:
            target = [
                x for x in targets if (x.df_port       == constraint['port'] ) and
                                      (x.df_port_index == constraint['index'])
            ]
            if len(target) != 1:
                raise ElaborationError(report.error(
                    f"Can't resolve target in address map for port "
                    f"{constraint['port'].hierarchicalPath()}[{constraint['index']}]"
                ), ph_doc=initiator)
            df_map.addConstraint(initiator.df_initiator, target[0].df_target)

    # Add constraints specified on the targets
    for target in targets:
        for constraint in target.df_constraints:
            initiator = [
                x for x in initiators if (x.df_port       == constraint['port'] ) and
                                         (x.df_port_index == constraint['index'])
            ]
            if len(initiator) != 1:
                raise ElaborationError(report.error(
                    f"Can't resolve initiator in address map for port "
                    f"{constraint['port'].hierarchicalPath()}[{constraint['index']}]"
                ), ph_doc=initiator)
            df_map.addConstraint(initiator[0].df_initiator, target.df_target)

    # Attach the address map to the block
    block.setAddressMap(df_map)
