# !His

The `!His` tag defines an interconnect type, which can carry multiple signals between a nominated 'master' and 'slave'. Signals within the interconnect can travel in either direction (i.e. from master to slave, or from slave to master), allowing complex bus connections to be expressed as a single port.

Each component of the `!His` can be a primitive signal, with a specified width ([!Port](./port.md)), or it can be a reference ([!HisRef](./hisref.md)) to another `!His`.

As every component, and indeed any sub-components when using a ([!HisRef](./hisref.md), can have a different role, the net role of each signal must be resolved recursively. For example:

```
MyHis [M-->S]
 |-- MyCompA [M-->S]
 |    |-- MySubCompA1 [M<--S]
 |    |-- MySubCompA2 [M-->S]
 |-- MyCompB [M<--S]
      |-- MySubCompB1 [M-->S]
      |-- MySubCompB2 [M<--S]
```

This arrangement results in the following net roles:

| Signal                    | Direction |
|---------------------------|-----------|
| MyHis.MyCompA.MySubCompA1 | `M<--S`   |
| MyHis.MyCompA.MySubCompA2 | `M-->S`   |
| MyHis.MyCompB.MySubCompB1 | `M<--S`   |
| MyHis.MyCompB.MySubCompB2 | `M-->S`   |

```eval_rst

.. warning::
   BLADE currently supports an attribute of `role` on a `!His` defintion - when set to `slave` it effectively reverses all of the logic when creating a port. However, this is unnecessary complication as you could instead change the role of the port on your block. As such, this attribute will be deprecated in the near future.
```

## Usage

```eval_rst
.. automodule:: blade.schema.ph_his
    :members:
    :special-members:
```