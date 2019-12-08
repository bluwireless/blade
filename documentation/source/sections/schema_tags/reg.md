# !Reg

The `!Reg` tag declares a single register within a [!Group](./group.md), listing its name, address, fields, access restrictions, and other properties.

BLADE's elaboration engine will use a number of stages to determine the address of a particular register:

 1. If an `addr` is provided, then the `!Reg` will be placed at the requested address. If operating in `BYTE` mode (see [!Group](./group.md) for more details) then this will be treated as a byte address, otherwise it will default to operating in word (4-byte) address mode.
 2. If no `addr` is given, but an `align` parameter is provided then the register will be placed at the next available word or byte address (depending on the group's mode) that agrees with the alignment requirement.
 3. If neither `addr` nor `align` is specified, then the register will be placed at the next  available address.

Registers have three different access constraints:

 * `blockaccess` specifies whether the block holding the register has the right to access or modify its value.
 * `busaccess` specifies whether the register can be accessed or modified from the bus connected to the register block, and whether strobe signals are required.
 * `instaccess` specifies whether instructions executing within the block can access or modify the register - this is useful when a block can execute some form of microcode.

The table below details which access types are valid in each scenario:

| Parameter   | W/WO | R/RO | RW | AW | AR | ARW | WS | WC |
|-------------|:----:|:----:|:--:|:--:|:--:|:---:|:--:|:--:|
| blockaccess | X    | X    | X  | -  | -  | -   | -  | -  |
| busaccess   | X    | X    | X  | X  | X  | X   | X  | X  |
| instaccess  | X    | X    | X  | -  | -  | -   | -  | -  |

*KEY: 'X' - valid combination, '-' - invalid combination*

The different access types are explained below:

 * `W`/`WO` - write-only access: valid should not be read as will return an invalid value.
 * `R`/`RO` - read-only access: any value written will be discarded. Value should always be kept constant between two consecutive reads unless a different transaction occurs in-between (i.e. value should not change of its own accord, or due to the fact it has been read).
 * `RW` - read-write access: value can be read or written and any value written will be preserved until it is over-written.
 * `AW` - active-write access: value can only be written, not read, and a strobe signal should be produced to qualify the written data.
 * `AR` - active-read access: value cannot modified by writing to the register, but can update as a result of reading from it as a strobe signal should be produced to qualify the read. This is suitable for applications such as popping from a FIFO.
 * `ARW` - active-read-write access: value can be both read and written, but there is no guarantee that any value written will be preserved. Strobe signals should be produced to qualify both read and write operations.
 * `WS` - write-set access: any bits at 1 in the written data will set the corresponding bits in the register, any bits at 0 in the written data will be ignored.
 * `WC` - write-clear access: any bits at 1 in the written data will clear the corresponding bits in the register, any bits at 0 in the written data will be ignored.

Another attribute the `!Reg` tag can have is its `location` - this details how the register should be implemented, and whether the auto-generated code or the hand-written implementation takes care of storing written values. The options for location are:

 * `internal` - register is handled within the auto-generated interface, storing the written value.
 * `wrapper` - register is handled by the wrapper around the auto-generated interface.
 * `core` - register is handled by the implementation of the block.

```eval_rst
.. warning::
    The `location` attribute may be deprecated in the future in favour of a clearer way of specifying how the register should be handled.
```

## Expansions

When BLADE is elaborating the register set, it can optionally expand registers into a collection of registers based upon flags within the `options` list. The following expansions are possible:

| Option   | Effect |
|----------|--------|
| EVENT    | Creates a set of registers for handling IRQs (masking, enables, sensitivity, etc.) |
| SETCLEAR | Creates three registers for handling set/clear masks of the value                  |

### Event Expansion
If the `EVENT` option is given, the register will be expanded into a number of registers each prefixed by the name given to the `!Reg` tag (position of the prefix is indicated below by an `X`):

 * `X_rsta` - Unmasked (raw) interrupt status,
 * `X_msta` - Masked version of the RSTA register using the enable register as a mask,
 * `X_clear` - Clears specific bits in the RSTA register (also updates MSTA),
 * `X_enable` - Enable specific interrupts to be active in the MSTA register (RSTA always active),
 * `X_set` - Set specific bits in the RSTA register (software triggered interrupts),
 * `X_level` - Defines interrupt sensitivity to be either high-level/rising-edge or low-level/falling-edge,
 * `X_mode` - Defines interrupt sensitivity mode to be either level or edge based.

To create an output IRQ signal, simply `AND` together the signals within the MSTA register.

```eval_rst
.. note::
   The `X_level` and `X_mode` registers are only present if the `HAS_LEVEL` and `HAS_MODE` options are present within the `!Reg`'s options array respectively. These registers only make sense when describing interrupt inputs to a block, so are not generated by default.
```

### Set-Clear Expansion
If the `SETCLEAR` option is given, the register will be expanded into three separate registers, each prefixed by the name given to the `!Reg` tag (position of the prefix is indicated below by an `X`):

 * `X` - the first register has exactly the same name as the `!Reg` tag, and acts just like a register with `busaccess` set to `RW` - i.e. it can be read and written to as normal.
 * `X_set` - when written, this register modifies the value of the `X` register, **setting** every bit in the register where a corresponding `1` is seen in the written value.
 * `X_clear` - when written, this register modifieis the value of the `X` register, **clearing** every bit in the register where a corresponding `1` is seen the in written value.

## Usage

```eval_rst
.. automodule:: blade.schema.ph_reg
    :members:
    :special-members:
```