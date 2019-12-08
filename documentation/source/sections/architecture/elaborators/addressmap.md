# Address Map Elaboration

Address maps can be attached to any module that performs some form of aggregation or distribution of the address space between multiple peripherals. Two different tags, [!Initiator](../../schema_tags/initiator.md) and [!Target](../../schema_tags/target.md), are used to describe the points of ingress and egress from the distributor or aggregator.

An address map can only describe the relationships between boundary ports of the block, it cannot describe the relationship between a boundary port and a port on a child block. This is because address distribution requires an implementation, and BLADE only supports implementation on leaf nodes.

The elaboration function has to be provided with a fully elaborated DFBlock instance, so that it can resolve references to boundary IO. It also needs to be given the list of [!Initiator](../../schema_tags/initiator.md) and [!Target](../../schema_tags/target.md) tags.

The stages the elaborator goes through are:

 1. Each port referenced by an `!Initiator` or `!Target` are resolved, with the signal index checked for validity. A check is also made that any ports referenced within the constraints section can be identified.
 2. Every target and initiator is converted to a `DFAddressMapTarget` or `DFAddressMapInitiator` and attached to an instance of `DFAddressMap`.
 3. Constraints specified in the original description are translated and resolved into the `DFAddressMap` - linking `DFAddressMapInitiators` and `DFAddressMapTargets`.

## API
```eval_rst
.. automodule:: blade.elaborate.address_map
    :members:
    :undoc-members:
```
