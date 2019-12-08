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
from . import reporting
report = reporting.get_report("elaborator")

# Import the different elaborators
from .elaborate.common import ElaborationError
from .elaborate.define import elaborate_define
from .elaborate.instruction import elaborate_instruction
from .elaborate.interconnect import elaborate_interconnect
from .elaborate.module import elaborate_module
from .elaborate.registers import elaborate_registers

# Import DesignFormat project
from designformat import DFProject

# Import Phhidle YAML schema types
from .schema import Config, Def, Group, His, Inst, Mod, Reg, Register

# Map tag types to elaboration functions
elaborators = {
    Config.__name__: elaborate_registers,
    Def.__name__   : elaborate_define,
    Group.__name__ : elaborate_registers,
    His.__name__   : elaborate_interconnect,
    Inst.__name__  : elaborate_instruction,
    Mod.__name__   : elaborate_module,
}

# List of types to ignore
ignored = []

def elaborate(top_docs, scope, max_depth=None):
    """ Elaborate described design from a top-level tag downwards.

    Run elaboration, starting from a Phhidle YAML schema object. Depending on the
    type of the schema object, different elaboration pathways are followed. All
    results are returned as a DesignFormat DFProject.

    Args:
        top_docs : The top level document to elaborate from
        scope    : An instance of ElaboratorScope that includes all documents
                 : parsed into the tool, allows references to be evaluated.
        max_depth: The maximum depth to elaborate to (optional, by default
                   performs a full depth elaboration - max_depth=None)

    Returns:
        DFProject: A DesignFormat project describing the elaborated design
    """
    # Separate !Config and !Group tags as these need special handling
    other_tags = [x for x in top_docs if type(x) not in [Group, Config, Reg]]
    reg_tags   = [x for x in top_docs if type(x) in     [Group, Config, Reg]]

    # Create a single project to return
    project = DFProject()

    # Work through all of the non-register tags
    for doc in other_tags:
        if type(doc) in ignored:
            report.debug(f"Ignoring top-level tag of type {type(doc).__name__}", item=doc)
            continue
        elif not type(doc).__name__ in elaborators:
            raise ElaborationError(
                report.error(f"Unsupported top level type {type(doc).__name__}", item=doc)
            )
        df_obj = elaborators[type(doc).__name__](doc, scope, max_depth=max_depth)
        if isinstance(df_obj, DFProject):
            project.mergeProject(df_obj)
        else:
            project.addPrincipalNode(df_obj)

    # Special handling for !Config and !Group tags
    if len(reg_tags) > 0:
        configs = [x for x in reg_tags if isinstance(x, Config)]
        if len(configs) == 0:
            config = Config([Register(x.name) for x in reg_tags if isinstance(x, Group)])
            configs.append(config)
        for reg_group in elaborate_registers(configs[0], scope):
            project.addPrincipalNode(reg_group)

    # Return the project
    return project
