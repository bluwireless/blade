# !Initiator

The `!Initiator` tag declares an initiator within a block's address map, this must refer to an existing *boundary* IO port on the block which handles the inbound bus traffic.

`!Initiators` have properties of `mask` and `offset`, which define the transformation applied to the inbound address by the port. For example you may have a specific address map within your SoC with absolute addresses, which can be mapped into a totally different point in the host system's memory - in this case you would mask out the sections required by your address map, and add any required offset.

You can also constrain an `!Initiator` so that it can only access certain end-points ([!Targets](./target.md)) by specifying a list of [!Point](./point.md) objects which refer to other boundary IO ports that have an associated `!Target` tag.

```eval_rst
.. warning::
   You can only make boundary IO ports on the block an `!Initiator` or a `!Target`, ports on child blocks cannot be promoted. This is because bus distribution components need an implementation and therefore are assumed to be leaf nodes.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_initiator
    :members:
    :special-members:
```