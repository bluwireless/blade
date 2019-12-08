# !Mod
The `!Mod` tag defines a module with a name, ports, child modules, interconnections, and other attributes. It can either represent a leaf module with implementation or a wiring level module with multiple, interconnected child nodes.

BLADE will modify its behaviour when elaborating a module based on values specified in the `options` array:

| Option | Effect |
|--------|--------|
| NO_AUTO_CLK_RST | Don't create implicit clock and reset signals for this block |
| NO_CLK_RST      | This block doesn't have any clock or reset signals, so don't try to auto-connect them when elaborating |
| IMP             | This block is a leaf node containing implementation |

Any leaf node can have a register map attached to it, this is done implicitly by `#include`'ing a register description into the same file as the `!Mod` definition - for example:

my_registers.yaml
```yaml
- !Config
  order:
  - !Register [config]

- !Group
  name: config
  regs:
  - !Reg
    name     : enable
    busaccess: RW
    fields   :
    - !Field
      name : switch
      width: 1
      lsb  : 0
      reset: 0
  ...
```

my_mod.yaml
```yaml

#include "my_registers.yaml"

- !Mod
  name   : my_mod
  sd     : My module with register map from my_registers.yaml
  options: [IMP]
  ...
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_mod
    :members:
    :special-members:
```