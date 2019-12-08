# !Connect

The `!Connect` tag defines a connection between ports of a block, as well as providing a mechanism to tie ports to a constant value. It is used within the `connections` section of the [!Mod](./mod.md) tag to define the interconnectivity of the boundary ports of the module and the ports of any child blocks.

When using the tag to describe interconnectivity, it is possible to express fan-ins, fan-outs, as well as 1-to-1 connections. It is important to understand the steps that the elaboration engine uses to build interconnections:

 * First it separates out all of the ports that are initiators (those that drive a value) and those that are targets (those that are driven).
 * Then it walks through the list of targets and assigns the next initiator in the sequence.
 * When it runs out of initiators, the engine wraps back to the first one in the list and begins allocating all over again.
 * The engine takes account of the number of instances of each port - so if the `count` parameter has been set to a number greater than 1, it will work through each target consecutively assigning the next available initiator before moving onto the next [!Point](./point.md) in the list. The same goes where the `count` for a specific initiator is greater than 1.

In the example shown in the usage section, 'switch_on' is a single signal that is being fanned out to four separate target ports ('inverter', 'and', and two instances of 'or'). Equally 'output' is a fan-in from four separate initiator ports on the same blocks.

If in a different example 'switch_on' instance had its `count` parameter set to 4, then one signal would have been uniquely connected to each of the sub-blocks.

```eval_rst
.. note::
   The order of the declaration is very important - as the first initiator will be assigned to the first target, the second initiator to the second target, and so on. Changing the order of `!Point` tags in the list will alter the resultant connectivity!
```

```eval_rst
.. warning::
   Only compatible signal types may be fanned-out or fanned-in - if you have a signal with bidirectional components (i.e. a `!His` containing both `master` and `slave` components) then it is not possible to fan-in or fan-out, only 1-to-1 connections are allowed as otherwise the drivers of each component would be unclear. The elaborator will raise an error if it encounters a mapping that it cannot comprehend.
```

When tying a port to a constant value, only one [!Const](./const.md) tag may be present in the list, but multiple [!Point](./point.md) tags may exist. Be aware that the constant value will only apply to any signal components driven by the parent block (i.e. those that will have a role of `master` relative to the block).

## Usage

```eval_rst
.. automodule:: blade.schema.ph_connect
    :members:
    :special-members:
```