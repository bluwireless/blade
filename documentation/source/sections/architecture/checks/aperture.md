# Rule Checking: Register Aperture Check

This check ensures that all registers of a block are accessible through the associated apertures in its parent hierarchy's address maps.

Take the example shown below where a single initiator port can access 4 different register blocks at different points in the address map - it is very important to be able to check that the initiator can access every register of every block.


```eval_rst
.. figure:: ../../../_static/images/Apertures.png
   :scale: 35 %
   :align: center
   :alt: Diagram of Address Map Apertures

   A simple address map with multiple layers of indirection
```

If we express a couple of the components of this design in YAML:

```yaml
- !Mod
  name : noc
  ports:
  - !HisRef [initiator, axi4, "Initiator port", 1, Slave]
  - !HisRef [target,    axi4, "Target ports",   2, Master]
  ...
  addressmap:
  - !Initiator
    mask: 0x0000FFFF
    port:
    - !Point [initiator]
  - !Target
    offset  : 0
    aperture: 0x1F0
    port    :
    - !Point [target, 0]
  - !Target
    offset  : 0x190
    aperture: 0xFE00
    port    :
    - !Point [target, 1]

- !Mod
  name : distributor_a
  ports:
  - !HisRef [inport,  axi4, "Input port",  1, Slave]
  - !HisRef [outport, ahb,  "Output port", 2, Master]
  ...
  addressmap:
  - !Initiator
    mask: 0x1FF
    port:
    - !Point [inport]
  - !Target
    offset  : 0
    aperture: 0x50
    port    :
    - !Point [outport, 0]
  - !Target
    offset  : 0x50
    aperture: 0x1B0
    port    :
    - !Point [outport, 1]
```

```eval_rst
.. note::
   Further information on the use of address maps and the `!Initiator` and `!Target` tags can be found in the schema section.
```

As shown above, the apertures for each register block are quite different - for example block 2 can expose 108 4-byte registers, whilst block 1 can only expose 20. Careful readers will have also noticed that the aperture in the NoC's address map is 16 bytes smaller than the sum of the apertures allocated in distributor A - although this isn't necessarily an issue provided that the aperture is not fully utilised.

If we now define a register set for block 1:

```yaml
- !Config
  order:
  - !Register [group_a]
  - !Register [group_b]

- !Group
  name: group_a
  regs:
  - !Reg
    name     : id
    busaccess: RO
    fields   :
    - !Field [value, 32, 0, "U", 0x12345678]
  ...
  - !Reg
    name       : scratch
    addr       : 0x1C
    array      : 2
    busaccess  : RW
    fields     :
    - !Field [value, 32, 0, "U", 0]
```

In this example, the second instance of the `scratch` register will be inaccessible through `distributor_a` - this is because two instances are requested (`array: 2`) and the base address is set at `0x1C`, placing the second instance at `0x20`.

As the check runs it will find the highest register address within each register block, it will then walk up the hierarchy checking whether the register is accessible based on the aperture size allocated to each target port. The check makes use of both connection chasing and any configured address maps to follow the connection as high up the hierarchy as possible.

```eval_rst
.. warning::
   This check shouldn't be treated as a guarantee that the address map is sane, as the implementation could substantially differ from the description within the YAML document. However, provided that you maintain your address map and register bank descriptions, it offers a useful early warning of potential issues.
```