# YAML Parser
BLADE's input syntax is comprised of specific YAML tags, each with a number of expected properties. The YAML syntax is extensive, and so is documented separately - the rest of this section gives a general overview of the parsing process.

For every supported tag, BLADE has an associated schema class to represent it. Basic properties of `name`, `options`, `ld`, and `sd` are common to almost all tag types - each tag then builds on these with its own specific properties.

Many tag types support both mapping and sequence node declarations. A mapping node representation uses a dictionary syntax similar to the following:

```YAML
- !Field
  name : my_field
  width: 4
  lsb  : 8
  type : U
  reset: 0
  ld   : "My long description of this field"
```

Whereas a sequence node uses an arrayed syntax, with the order of arguments being critical:

```YAML
- !Field [my_field, 4, 8, U, 0, "My long description of this field"]
```

The parser supports mapping and sequence nodes for all tag types, the order of the parameters is defined by the order they appear in the schema class' initiator. Optional parameters can simply be left blank or not listed.

The parser enforces that only one definition of each parameter exists per tag instance and will raise an error if repetition is detected. For example, the following declaration would be illegal due to the reptition of the 'enums' field.

```YAML
- !Field
  name : my_field
  width: 4
  lsb  : 8
  reset: 0
  enums:
  - !Enum [my_enum_val_0]
  enums: # <-- Illegal second definition
  - !Enum [my_enum_val_1]
```

As seen above, tags may be used as child attributes of a tag field if supported. These will be strictly type checked in the validation stage.

```eval_rst
.. note::
    During the parsing stage, no effort is made to verify the 'correctness' of the design nor of the syntax beyond complying with the basic YAML language, instead this is performed in a later stage.
```

## API
```eval_rst
.. automodule:: blade.parser
    :members:
    :undoc-members:
```