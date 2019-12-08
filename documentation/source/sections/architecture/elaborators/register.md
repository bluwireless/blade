# Register Elaboration

The register set for a block is described in the YAML schema by [!Config](../../schema_tags/config.md), [!Group](../../schema_tags/group.md), and [!Reg](../../schema_tags/reg.md) tags. These are elaborated into `DFRegisterGroups` and `DFRegisters` by BLADE, resolving all addresses and flattenning out any repetitions (where `array` is greater than 1).

The elaboration works over a few stages to build the final register set:

 1. The first stage is to identify or generate a `!Config` tag, which specifies the order that the `!Groups` should be instantiated. If one can be found in the document scope then it is used, otherwise one is automatically created - placing all non-macro groups in the same order that they are declared in the file.
 2. Then the elaborator works through each entry in the config:
    * For each [!Register](../../schema_tags/register.md) tag, the referenced `!Group` is instantiated just once starting at the next available address.
    * For each [!Macro](../../schema_tags/macro.md) tag, the referenced `!Group` is instantiated as many times as the tag requests using the specified prefix. It is placed starting at the next available address that agrees with the `align` constraint.
 3. For each placed `!Group` instance a `DFRegisterGroup` is created, and the elaborator works through the register list converting each `!Reg` to a `DFRegister` and attaching it to the group. Each register will be placed at the next available address that agrees with its `align` parameter, unless an explicit `addr` is specified in which case the address will be forced. Overlaps between registers are detected and an exception will be thrown to abort the elaboration, details of the conflict will be included in the error message.
    * If a register has one of the expansion options (see below), then it will be expanded as the first stage of handling the group. This allows the rest of the elaboration process to continue as if the registers had been present in the original description.
 4. For each `!Reg` placed as a `DFRegister` within the group the elaborator works through the associated [!Field](../../schema_tags/field.md) list and creates `DFRegisterFields`. By default each field will be placed at the next available least-significant bit, but an `lsb` parameter can be provided to force a certain position. Overlaps between fields are detected and an exception will be thrown to abort the elaboration, details of the fields that conflict will be included in the error message.

Further details on the exact placement of registers and fields can be found in the source code for the register elaborator.

## Expansions
If certain keys are present within the `options` array for a `!Reg` then the elaborator will change its behaviour. These are:

| Option   | Effect |
|----------|--------|
| event    | Requires interrupt handling registers such as MSTA and RSTA |
| setclear | Requires set-clear registers such as SET, CLEAR, and STATUS |

Further details on what these expansions do can be found in the schema documentation for the [!Reg tag](../../schema_tags/reg.md). The API for the expansion functions can be seen below.

## API
```eval_rst
.. automodule:: blade.elaborate.registers
    :members:
    :undoc-members:
```

## API: Event Expansion
```eval_rst
.. automodule:: blade.elaborate.register_interrupt
    :members:
    :undoc-members:
```

## API: Set-Clear Expansion
```eval_rst
.. automodule:: blade.elaborate.register_setclear
    :members:
    :undoc-members:
```