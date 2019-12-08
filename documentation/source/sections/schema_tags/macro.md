# !Macro
The `!Macro` tag is used within the order section of a [!Config](./config.md) tag to specify the position that a macro type register [!Group](./group.md) should be instantiated.

Unlike when using a [!Register](./register.md) tag, when using a `!Macro` the same register [!Group](./group.md) can be instantiated multiple times - each time controlling the number of instantiations (using the `array` parameter) and the word alignment of the base of each instantiation (using the `align` parameter).

```eval_rst
.. note::
   Only !Groups with their `type` attribute set to `macro` can be instantiated using the !Macro tag.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_macro
    :members:
    :special-members:
```