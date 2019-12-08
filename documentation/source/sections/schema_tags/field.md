# !Field

The `!Field` tag declares a single field within a [!Reg](./reg.md) or [!Inst](./inst.md) declaration, providing a way to split the full width of register up into meaningful sub-divisions. It's very useful for packing multi pieces of related information into a word that's retrievable with a single fetch.

Placement of the `!Field` within the register's width can be controlled by using the `lsb` (least-significant bit) and `msb` (most-significant bit) parameters. If both parameters are omitted then the field will be placed with its least-significant bit at the first available position, following the order that the `!Fields` have been declared in the [!Reg](./reg.md) or [!Inst](./inst.md) tag's `field` list.

```eval_rst
.. warning:
   Although you can specify the `width, `lsb`, and `msb` parameters, you must make sure that they all agree. If they disagree, then the elaborator will raise an exception. The elaborator does not attempt to calculate a `width` from a provided `msb` and `lsb` pair, and if its omitted from the description it will take a default value of `1`.
```

Where a field is used to represent a discrete value, it can be enumerated using [!Enum](./enum.md) tags - allowing a name to be associated with a particular value, along with a description of its purpose.

```eval_rst
.. warning:
   If the highest allocated bit within a field exceeds the stated width of the register, then the elaborator will raise a warning and automatically extend the register's width. However be aware that if your implementation expects a certain data word width that these fields may become inaccessible.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_field
    :members:
    :special-members:
```