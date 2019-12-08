# !Port

The `!Port` tag describes a primitive component within an interconnect (declared as a ([!His](./his.md)). A `!Port` offers a basic name, width, count, default value, and role.

`!Port`s can be declared with one of two roles of either `master` or `slave`:

 * As a `master` it carries data from an initiator [!Mod](./mod.md) with the parent port declared as a `master`, to the target [!Mod](./mod.md) with the parent port declared as a `slave`
 * As a `slave` it carries data from a target [!Mod](./mod.md) with the parent port declared as a `slave`, to an initiator [!Mod](./mod.md) with the parent port declared as a `master`.

Ports with different roles can be mixed within the same [!His](./his.md) definition along with [!HisRef](./hisref.md) tags.

You can optionally define an enumeration for the different values the signal can take using the [!Enum](./enum.md) tag.

## Usage

```eval_rst
.. automodule:: blade.schema.ph_port
    :members:
    :special-members:
```