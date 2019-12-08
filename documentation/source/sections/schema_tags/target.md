# !Target

The `!Target` tag declares a target within a block's address map, this must refer to an existing *boundary* IO port on the block which handles the outbound bus traffic.

`!Targets` have properties of `offset` and `aperture`, which define the absolute address window that each outbound port can be accessed through. Remember to take into account the masking and offset applied to the inbound address by the [!Initiator](./initiator.md) tag.

You can also constrain an `!Target` so that it can only be accessed by certain ([!Initiators](./initiator.md)) by specifying a list of [!Point](./point.md) objects which refer to other boundary IO ports that have an associated `!Initiator` tag.

```eval_rst
.. warning::
   You can only make boundary IO ports on the block an `!Initiator` or a `!Target`, ports on child blocks cannot be promoted. This is because bus distribution components need an implementation and therefore are assumed to be leaf nodes.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_target
    :members:
    :special-members:
```