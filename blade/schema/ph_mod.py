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

    - !Mod
      name       : my_module
      sd         : Short description of my module
      ld         : >
        Longer description of my module that can span multiple lines.
      options    : []
      # Declare boundary ports for this module
      ports      :
      - !HisRef [cfg,      axi4,        "Configuration port",    1, Slave,  "AXI4-Lite configuration port",                      []]
      - !HisRef [bypass,   enable,      "Input bypass signal",   1, Slave,  "Disables the block - data passes straight through", []]
      - !HisRef [data_in,  axi4_stream, "Streaming data input",  1, Slave,  "Inbound data to the block",                         []]
      - !HisRef [data_out, axi4_stream, "Streaming data output", 1, Master, "Outbound data from the block",                      []]
      # Declare child modules
      modules    :
      - !ModInst [convert,   axi4_to_axi4l, "AXI4 to AXI4-Lite", 1, "Converts from AXI4 to AXI4-Lite",  []]
      - !ModInst [registers, my_reg_blk,    "Register block",    1, "Controls for the transform block", []]
      # Declare explicit connections (for where autoconnections won't work)
      connections:
      # - Connect boundary AXI4 configuration port to the AXI4 to AXI4-Lite converter
      - !Connect
        points:
        - !Point [cfg]
        - !Point [inport, convert]
      # - Connect output of the converter to the input of the register block
      - !Connect
        points:
        - !Point [outport, convert  ]
        - !Point [cfg,     registers]
      # Tie-off unused boundary ports (where they don't connect to a child)
      defaults:
      - !Point [bypass]
"""

from .ph_tag_base import TagBase, ValidationError, CONSTANTS

from .. import reporting
report = reporting.get_report("schema.mod")

# For validation
from .ph_his_ref import HisRef
from .ph_initiator import Initiator
from .ph_mod_inst import ModInst
from .ph_connect import Connect
from .ph_point import Point
from .ph_target import Target

class Mod(TagBase):
    """ !Mod tag schema class listing ports, modules, and interconnections """
    yaml_tag = "!Mod"

    def __init__(
        self,
        name,
        ports,
        options       = None,
        sd            = "",
        modules       = [],
        connections   = [],
        conections    = [],     # Alias for 'connections' to support legacy behaviour
        ld            = "",
        defaults      = [],
        importhisrefs = None,   # TODO: Remove deprecated?
        requirements  = None,   # TODO: Remove deprecated?
        clk_root      = None,
        rst_root      = None,
        addressmap    = None,
        extends       = None,   # Allow a block to extend the definition of another
    ):
        """ Initialisation for !Mod YAML Tag

        Args:
            name         : Name of the !Mod, how it will be referred to when instantiated
            ports        : List of !HisRef ports on the boundary of this block
            options      : List of options either in the form 'KEY=VAL' or just 'KEY' if
                           a value is not required
            sd           : Short description of the block - maximum 150 characters
            modules      : List of !ModInst tags which instantiate child modules
            connections  : List of !Connect tags detailing connections between
                           ports of the block and ports of child blocks
            conections   : Deprecated alias of 'connection'
            ld           : Long description of the block - no maximum length
            defaults     : List of !Point tags that tie-off unused input and output
                           ports
            importhisrefs: Deprecated attribute
            requirements : Deprecated attribute
            clk_root     : !Point tag specifying which (if any) output port on
                           the block acts as a clock generator.
            rst_root     : !Point tag specifying which (if any) output port on
                           the block acts as a reset generator.
            addressmap   : A list of !Initiator and !Target tags detailing the
                           address map between input and output ports.
            extends      : Allow block to inherit and extend the definition
                           (ports, connections, etc.) of another defined !Mod.
        """
        super().__init__(name, sd, ld, options)

        self.ports       = (ports if ports != None else [])
        self.modules     = (modules if modules != None else [])

        # NOTE: Alias 'conections' -> 'connections'
        self.connections = connections if connections and len(connections) > 0 else conections
        if self.connections == None: self.connections = []

        self.defaults      = (defaults if defaults != None else [])
        self.importhisrefs = importhisrefs
        self.clk_root      = clk_root
        self.rst_root      = rst_root
        self.requirements  = requirements
        self.extends       = extends.strip() if isinstance(extends, str) else extends
        self.addressmap    = addressmap

    def set_source_file(self, file):
        """ Set the source file of this object and propagate it to children.

        Args:
            file: The source file path or object
        """
        super().set_source_file(file)
        for port in self.ports:
            port.set_source_file(file)
        for module in self.modules:
            module.set_source_file(file)
        for connection in self.connections:
            connection.set_source_file(file)
        if self.clk_root:
            for point in self.clk_root:
                point.set_source_file(file)
        if self.rst_root:
            for point in self.rst_root:
                point.set_source_file(file)
        if self.addressmap:
            for node in self.addressmap:
                node.set_source_file(file)

    def set_file_marks(self, start, end):
        """ Set start and end marks of the declaration and propagate to children

        Args:
            start: The starting mark
            end  : The ending mark
        """
        for port in self.ports:
            if self.start_mark:
                port.shift_file_marks(start.line - self.start_mark.line)
            else:
                port.set_file_marks(start, end)
        for module in self.modules:
            if self.start_mark:
                module.shift_file_marks(start.line - self.start_mark.line)
            else:
                module.set_file_marks(start, end)
        for connection in self.connections:
            if self.start_mark:
                connection.shift_file_marks(start.line - self.start_mark.line)
            else:
                connection.set_file_marks(start, end)
        if self.clk_root:
            for point in self.clk_root:
                if self.start_mark:
                    point.shift_file_marks(start.line - self.start_mark.line)
                else:
                    point.set_file_marks(start, end)
        if self.rst_root:
            for point in self.rst_root:
                if self.start_mark:
                    point.shift_file_marks(start.line - self.start_mark.line)
                else:
                    point.set_file_marks(start, end)
        if self.addressmap:
            for node in self.addressmap:
                if self.start_mark:
                    port.shift_file_marks(start.line - self.start_mark.line)
                else:
                    port.set_file_marks(start, end)
        super().set_file_marks(start, end)

    def validate(self):
        """ Check that this tag agrees with our YAML schema """
        # Perform validation of TagBase first
        super().validate()

        # Check that 'ports' is a list only containing HisRef objects
        if self.ports != None:
            if not isinstance(self.ports, list):
                raise ValidationError(
                    report.error("Module ports are not stored as a list", item=self),
                    "ports", self
                )
            bad = [x for x in self.ports if not isinstance(x, HisRef)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Module ports contains {bad[0].yaml_tag}", item=self),
                    "ports", self
                )
            # Validate all ports
            for port in self.ports:
                port.validate()
            # Check that if a port specifies 'AUTO_CLK' or 'AUTO_RST' then we
            # have a 'NO_AUTO_CLK_RST' option on the !Mod
            has_auto    = (CONSTANTS.OPTIONS.NO_AUTO_CLK_RST not in (x.lower() for x in self.options))
            has_clk_rst = (CONSTANTS.OPTIONS.NO_CLK_RST      not in (x.lower() for x in self.options))
            for port in self.ports:
                if CONSTANTS.OPTIONS.AUTO_CLK in (x.lower() for x in port.options):
                    if has_auto and has_clk_rst:
                        raise ValidationError(
                            report.error(f"Port {port.name} is nominated as 'AUTO_CLK', but 'NO_AUTO_CLK_RST' is not specified", item=self),
                            "ports", self
                        )
                elif CONSTANTS.OPTIONS.AUTO_RST in (x.lower() for x in port.options):
                    if has_auto and has_clk_rst:
                        raise ValidationError(
                            report.error(f"Port {port.name} is nominated as 'AUTO_RST', but 'NO_AUTO_CLK_RST' is not specified", item=self),
                            "ports", self
                        )

        # Check that 'modules' is a list only containing ModInst objects
        if self.modules != None:
            if not isinstance(self.modules, list):
                raise ValidationError(
                    report.error("Module sub-modules are not stored as a list", item=self),
                    "modules", self
                )
            bad = [x for x in self.modules if not isinstance(x, ModInst)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Module sub-modules contains {bad[0].yaml_tag}", item=self),
                    "modules", self
                )
            # Validate all modules
            for module in self.modules:
                module.validate()

        # Check that 'connections' is a list only containing Connect objects
        if self.connections != None:
            if not isinstance(self.connections, list):
                raise ValidationError(
                    report.error("Module connections are not stored as a list", item=self),
                    "connections", self
                )
            bad = [x for x in self.connections if not isinstance(x, Connect)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Module connections contains a {bad[0].yaml_tag}", item=self),
                    "connections", self
                )
            # Validate all connections
            for connect in self.connections:
                connect.validate()

        # Check that 'defaults' is a list only containing Point objects
        if self.defaults != None:
            if not isinstance(self.defaults, list):
                raise ValidationError(
                    report.error("Module defaults are not stored as a list", item=self),
                    "defaults", self
                )
            bad = [x for x in self.defaults if not isinstance(x, Point)]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Module defaults contains a {bad[0].yaml_tag}", item=self),
                    "defaults", self
                )
            # Validate all defaults
            for default in self.defaults:
                default.validate()

        # If 'clk_root' is present, check that it is a Point object
        if self.clk_root != None:
            # NOTE: Some files specify clk_root as an array, accept single entry arrays
            if isinstance(self.clk_root, list) and len(self.clk_root) == 1:
                self.clk_root = self.clk_root[0]
            if not isinstance(self.clk_root, Point):
                raise ValidationError(
                    report.error("Module clk_root is not declared as a !Point", item=self),
                    "clk_root", self
                )
            else:
                self.clk_root.validate()

        # If 'rst_root' is present, check that it is a Point object
        if self.rst_root != None:
            # NOTE: Some files specify clk_root as an array, accept single entry arrays
            if isinstance(self.rst_root, list) and len(self.rst_root) == 1:
                self.rst_root = self.rst_root[0]
            if not isinstance(self.rst_root, Point):
                raise ValidationError(
                    report.error("Module rst_root is not declared as a !Point", item=self),
                    "rst_root", self
                )
            else:
                self.rst_root.validate()

        # If 'extends' is present, check that it is a valid string
        if self.extends != None:
            if not isinstance(self.extends, str):
                raise ValidationError(
                    report.error("Module extends must be a string", item=self),
                    "extends", self
                )

        # Check that 'addressmap' is a list only containing Initiator & Target
        if self.addressmap != None:
            if not isinstance(self.addressmap, list):
                raise ValidationError(
                    report.error("Module addressmap are not stored as a list", item=self),
                    "addressmap", self
                )
            bad = [x for x in self.addressmap if type(x) not in [Initiator, Target]]
            if len(bad) > 0:
                raise ValidationError(
                    report.error(f"Module addressmap contains a {bad[0].yaml_tag}", item=self),
                    "addressmap", self
                )
            # Validate all addressmap
            for default in self.addressmap:
                default.validate()
