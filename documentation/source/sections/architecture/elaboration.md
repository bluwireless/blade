# Elaboration
In the elaboration phase the "root" YAML document is examined and any modules, interconnect types, registers, instructions, or defined values are evaluated to construct DesignFormat nodes.

There are different elaboration pathways depending on the type of the root document:

 * `!Mod`: Module definitions are evaluated to form `DFBlock` nodes - expanding hiearchy and interconnects, as well as attaching any included register definitions. Depending on the depth specified to elaboration, it will either perform a shallow (limited number of levels of hierarchy expanded) or full-depth (every layer of hierarchy expanded).
 * `!Config` or `!Group`: Register definitions are expanded into `DFRegisterGroup` and `DFRegister` nodes. If a `!Config` tag is present within the root file, then register groups will be instantiated in the order specified. If a `!Config` tag is not present, then register groups will be instantiated in the order they are declared in the file.
 * `!Def`: Constant definitions are fully evaluated (i.e. all cross-references and arithmetic are evaluated) to form `DFDefine` nodes.
 * `!His`: Interconnect definitions are expanded to form `DFInterconnect` and `DFInterconnectComponent` nodes.
 * `!Inst`: Instruction definitions are fully evaluated to form `DFCommand` nodes. Note that all inheritance is evaluated, so every field of the instruction is represented in the `DFCommand` whether or not it is inherited (however inherited fields have the attribute of `inherited` set to `true`).

The different pathways are discussed in further this section, with the rules of the expansions explained:

```eval_rst
.. toctree::
    :maxdepth: 2

    elaborators/module
    elaborators/addressmap
    elaborators/interconnect
    elaborators/register
    elaborators/instruction
```