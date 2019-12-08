# !Config

The `!Config` tag defines the order of register groups within a register set - two different tags can be used within the order:
 * [!Register](./register.md) - specifies the position that a normal [!Group](./group.md) should be instantiated within the register set. Each group can be instantiated uniquely, and uses the same name as it's declaration.
 * [!Macro](./macro.md) - specifies the position that a macro [!Group](./group.md) (i.e. one with `type=MACRO`) should be instantiated within the register set, along with `array` and `align` parameters for controlling the number of instances and the word alignment for each. A macro group can be instantiated multiple times, each time using the name provided in the [!Macro](./macro.md) declaration.

## Usage

```eval_rst
.. automodule:: blade.schema.ph_config
    :members:
    :special-members:
```

