# !Define

The `!Define` tag is used to override specific parameters of a register within a known register group. They are particularly useful where the same register description is reused in multiple places but some parameter (e.g. the `blockaccess` attribute) needs to be different in one implementation than another.

For any attributes that do not have `!Define` overrides, they maintain the same value that they took in the base register description.

Descriptions of [!Reg](./reg.md) and [!Field](./field.md) attributes can be found in their schema descriptions.

```eval_rst
.. note::
   The `!Define` tag is likely to be refactored into an `!Override` tag that can be used more widely than just for register descriptions, and may form the basis of parameterisable components within BLADE.
```

Below is a more detailed example than normal to try and explain how this tag is used, and why it exists.

## Example

**base_registers.yaml:**
```yaml
- !Group
  name: group_a
  regs:
  - !Reg
    name     : device_id
    busaccess: RO
    reset    : 0x12345678
    ...
  ...

- !Group
  name: group_b
  regs:
  - !Reg
    name : data_words
    width: 16
    array: 4
    ...
  ...
```

**first_mod.yaml:**
Here we alter the device ID and make it active-read, so that a strobe signal is fired every time the register is read.

```yaml
#include "base_registers.yaml"

- !Config
  order:
  - !Register [group_a]
  - !Register [group_b]

- !Define { group: group_a, reg: device_id, reset: 0x11223344, busaccess: AR }
```

**second_mod.yaml:**
Here we change the device ID, then widen the data words whilst keeping the same overall number of bits by decreasing the array size.

```yaml
#include "base_registers.yaml

- !Config
  order:
  - !Register [group_b]
  - !Register [group_a]

- !Define { group: group_a, reg: device_id, reset: 0x99887766 }
- !Define { group: group_b, reg: data_words, width: 32, array: 2 }
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_define
    :members:
    :special-members:
```