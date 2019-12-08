# !HisRef

The `!HisRef` tag is used in two different scenarios:

 * For [!His](./his.md) declarations this tag is used to add complex components to interconnect definitions, which reference other pre-defined [!His](./his.md).
 * For [!Mod](./mod.md) declarations this tag is used to declare the boundary ports using a specific, pre-defined [!His](./his.md).

When used as a 'port' within a [!His](./his.md) declaration, just as with [!Port](./port.md) declarations, the tag can either have a `master` or `slave` role:

 * As a `master` it will predominantly carry data from an initiator [!Mod](./mod.md) with the parent port declared as a `master`, to the target [!Mod](./mod.md) with the parent port declared as a `slave`
 * As a `slave` it will predominantly carry data from a target [!Mod](./mod.md) with the parent port declared as a `slave`, to an initiator [!Mod](./mod.md) with the parent port declared as a `master`.

When used as a 'port' on a [!Mod](./mod.md) the tag can also have `master` or `slave` roles but the meaning is slightly different:

 * As a `master` it is an initiator port, one that will predominantly drive the signal components within the interconnect.
 * As a `slave` it is a target port, one that predominantly receives the driven value of signal components within the interconnect.

When being used as a port, a number of options can influence the behaviour of BLADE's elaboration engine:

| Option   | Effect |
|----------|--------|
| AUTO_CLK | Nominates the port as the default clock signal to be connected in the parent block, and distributed to any child nodes. |
| AUTO_RST | Nominates the port as the default reset signal to be connected in the parent block, and distributed to any child nodes. |

## Usage

```eval_rst
.. automodule:: blade.schema.ph_his_ref
    :members:
    :special-members:
```