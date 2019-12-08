# !Point

The `!Point` tag identifies either a boundary port on the block, or one of the ports on a child module. It is used in two roles:

 * When used within the [!Connect](./connect.md) tag, or in the `defaults` list of a [!Mod](./mod.md) tag, it can identify any port on the block or on a instantiated child block (but not select a specific instance within that port).
 * When used within the [!Initiator](./initiator.md) or [!Target](./target.md) tags it can only identify a specific index of a port on the boundary of the block (i.e. it can identify a specific instance of a port from a [!HisRef](./hisref.md) with `count` greater than 1).

## Usage

```eval_rst
.. automodule:: blade.schema.ph_point
    :members:
    :special-members:
```