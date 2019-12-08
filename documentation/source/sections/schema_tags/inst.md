# !Inst

The `!Inst` tag declares an instruction that can be extended to form an instruction set. It is useful for declaring CPU instruction set extensions, or microcode instructions for a accelerator engine.

```eval_rst
.. warning::
   This tag is likely to be refactored into a more generic !Command description tag, that builds on the ideas of 'extending' a base tag to add more functionality. This would be more suited to other uses than the existing !Inst instruction description - with the current implementation only one field can be overridden or fixed to a value per instruction layer, this is likely to be replaced with a more flexible mechanism.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_inst
    :members:
    :special-members:
```