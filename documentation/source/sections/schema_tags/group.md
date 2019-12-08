# !Group

The `!Group` tag declares a register group - a collection of registers that can be instantiated as a single object within a register set, with the position of the group within the set being controlled by the [!Config](./config.md) tag.

Two different types of `!Group` exist:

 * `REGISTER` or 'normal' type groups can be instantiated uniquely within a register set, these are the default behaviour but can be explicitly declared by setting the `type` attribute to `register`.
 * `MACRO` type groups can be instantiated multiple times, each time using prefix, array, and alignment parameters provided by the [!Macro](./macro.md) tag.

`!Groups` contain a list of [!Reg](./reg.md) tags which declare the actual registers, which in turn contain a list of [!Field](./field.md) tags which declare the variable width fields that make up the register.

BLADE will modify its behaviour when elaborating a register group based on values specified in the `options` array:

| Option | Effect |
|--------|--------|
| BYTE   | Register addresses and alignments will be treated as byte values rather than word |

```eval_rst
.. note::
   By default, the elaborator will treat all register addresses and alignment requirements as word addresses (i.e. 4-byte wide). However, this behaviour can be changed to instead treat these values as byte addresses by using the `BYTE` option as described above.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_group
    :members:
    :special-members:
```