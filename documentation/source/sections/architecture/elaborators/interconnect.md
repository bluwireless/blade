# Interconnect Elaboration

Interconnections are described in BLADE using [!His](../../schema_tags/his.md) tags - these can contain multiple named components, each of which can either be primitive ([!Port](../../schema_tags/port.md)) or complex ([!HisRef](../../schema_tags/hisref.md)), in which case they instantiate another [!His](../../schema_tags/his.md) as a subcomponent.

For each [!His](../../schema_tags/his.md) definition, a `DFInterconnect` node will be created within the project. For each component:

 * [!Ports](../../schema_tags/port.md) will be converted to a **simple** `DFInterconnectComponent` with a fixed width. If an enumeration is present, then it will be attached to the component.
 * [!HisRefs](../../schema_tags/hisref.md) will be converted to a **complex**
 `DFInterconnectComponent` with a reference to the instantiated `DFInterconnect`.

Any values declared within the `options` array will be transferred to attributes of the `DFInterconnect`.

## API
```eval_rst
.. automodule:: blade.elaborate.interconnect
    :members:
    :undoc-members:
```