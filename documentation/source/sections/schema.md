# YAML Schema
BLADE is driven by a description of the design written in a custom YAML schema. Different tags address different needs, for example `!Mod` details a module with a name, ports, child modules, and interconnections while `!His` defines an interconnect type which can carry multiple signals with different roles.

This section of the documentation details each schema tag, along with examples of how they may be used.

## Tags
 * [!Config](schema_tags/config) - specifies the order of groups within a register set.
 * [!Connect](schema_tags/connect) - defines interconnectivity between ports and constant values.
 * [!Const](schema_tags/const) - describes a constant value tie for a port.
 * [!Define](schema_tags/define) - overrides parameters of [!Reg](schema_tags/reg) and [!Field](schema_tags/field) tags at instantiation
 * [!Def](schema_tags/def) - defines a named value that can be used throughout the design.
 * [!Enum](schema_tags/enum) - discretises a register field into named integer integers.
 * [!Field](schema_tags/field) - breaks a register's width up into meaningful sub-divisions.
 * [!Group](schema_tags/group) - declares a register group
 * [!His](schema_tags/his) - a complex interconnect declaration
 * [!HisRef](schema_tags/hisref) - instantiating of an interconnect as a port or component
 * [!Initiator](schema_tags/initiator) - identifies address map accessible from a certain port
 * [!Inst](schema_tags/inst) - used to describe a microcode instruction set
 * [!Macro](schema_tags/macro) - instantiates a macro type register group
 * [!ModInst](schema_tags/modinst) - instantiates a !Mod as a child of another block
 * [!Mod](schema_tags/mod) - declaration of a module with ports and submodules
 * [!Point](schema_tags/point) - identifies a boundary port on a module or sub-module
 * [!Port](schema_tags/port) - a simple component of an interconnect
 * [!Register](schema_tags/register) - instantiates a normal register group (non-macro)
 * [!Reg](schema_tags/reg) - declares a single register within a group
 * [!Target](schema_tags/target) - specifies window in the address map to access a certain port

```eval_rst
.. Declare a real ToC so that we can navigate using the sidebar, but make it hidden so we can use the custom version above - which has descriptions for each item!
.. toctree::
    :maxdepth: 1
    :hidden:

    schema_tags/config
    schema_tags/connect
    schema_tags/const
    schema_tags/define
    schema_tags/def
    schema_tags/enum
    schema_tags/field
    schema_tags/group
    schema_tags/his
    schema_tags/hisref
    schema_tags/initiator
    schema_tags/inst
    schema_tags/macro
    schema_tags/modinst
    schema_tags/mod
    schema_tags/point
    schema_tags/port
    schema_tags/register
    schema_tags/reg
    schema_tags/target
```

## Deprecated Tags
The following tag types have been deprecated, but support has not yet been fully removed from BLADE. Do not use these tag types in new designs.

 * `!File` - creates a new requirements document.
 * `!Req` - declares a requirement.
 * `!Spec` - declares a specific document.
 * `!Unroll` - internal tag used by previous version of tool.
 * `!Map` - declared mapping between Verilog and BLADE components.

```eval_rst
.. warning::
   Support for these tag types may be wholly or partially missing from BLADE's elaboration engine, however it will consume them in order to maintain compatibility with older designs. They will be fully removed in future revisions.
```