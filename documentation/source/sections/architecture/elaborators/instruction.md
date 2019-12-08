# Instruction Elaboration

Instruction sets can be defined by using the [!Inst](../../schema_tags/inst.md) tag. Instructions can inherit from one another, fixing the value of one enumerated field per level - in this way fields do not have to be replicated between definitions.

Instruction elaboration works in two phases:

 * In the first phase the elaborator collapses the inheritance list of a instruction to form a single description of the [!Inst](../../schema_tags/inst.md) with all of inherited [!Fields](../../schema_tags/field.md) populated and with all fixed values resolved.
 * In the second phase the instruction definition is converted into a `DFCommand` containing `DFCommandFields` - in this stage all placements are evaluated, and any overlaps between fields are detected and raised as exceptions.

Any field enumerations are transferred through into the DesignFormat description, and any values within the `options` list are transferred through as `attributes`.

```eval_rst
.. warning::
   This !Inst tag is likely to be refactored into a more generic !Command description tag, that builds on the ideas of 'extending' a base tag to add more functionality. This would be more suited to other uses than the existing !Inst instruction description - with the current implementation only one field can be overridden or fixed to a value per instruction layer, this is likely to be replaced with a more flexible mechanism.
```

## API
```eval_rst
.. automodule:: blade.elaborate.instruction
    :members:
    :undoc-members:
```