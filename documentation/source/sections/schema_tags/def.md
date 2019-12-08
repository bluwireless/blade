# !Def

The `!Def` tag defines a integer value that can then be used in place of any constant within the design description. For example it can be used to define the width of a data bus, which can then be used in any [!His](./his.md) that carries data as the `width` parameter.

It is preferable to make use of `!Def` tags as widely as possible, as it makes modifying parameters of the overall design far easier (rather than editing every file separately).

`!Def` tags are treated as first-class citizens, so they will be converted into `DFDefines` and attached the DesignFormat project. This means you can autogenerate a list of defined values in any language you write your implementation in.

```eval_rst
.. note::
    In the future `!Def` and `!Const` tags may be merged into one new tag in order to reduce complexity of the schema.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_def
    :members:
    :special-members:
```