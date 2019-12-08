# !ModInst

The `!ModInst` tag instantiates a [!Mod](./mod.md) description as a child module of the block. The same [!Mod](./mod.md) may be instantiated multiple times, each time with a different name. Once the instance is declared, interconnectivity can be specified using the [!Connect](./connect.md) tag.

If more than one instance of a particular block is required for creating parallel, identical, data paths then you can use the `count` parameter to instantiate multiple instances with the same name. This makes declaration of interconnections much easier, as both instances can be hooked up with a single statement (see [!Connect](./connect.md) for further details).

## Usage

```eval_rst
.. automodule:: blade.schema.ph_mod_inst
    :members:
    :special-members:
```