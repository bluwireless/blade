# Rule Checking

Rule checks are executed as the final stage of the workflow, allowing automated tests to be run against the fully elaborated design to introspect it and check for problems. The checking system is designed to be extensible, with rules being automatically detected and integrated at runtime.

## Existing Checks
BLADE includes a number of built-in checks, documentation for these can be found separately:

```eval_rst
.. toctree::
    :maxdepth: 1

    checks/aperture.md
```

## Waiving Rule Violations
As BLADE's rule checks are automated, it may be possible for false-positives to arise - this may occur when rules are particularly strict, and easily broken. Rather than force the developer to weaken the check, BLADE provides a waiver mechanism to say that a particular issue can be ignored - this will downgrade the violation (critical or not) into just a warning.

Paths to waiver files can be provided as a list when calling `build_project` by using the `waivers` argument. Every waiver file is combined into a single waiver list which is then used by the checker framework.

A waiver file is nothing more than a list of MD5 hashes which represent particular error conditions, comments can be used to make the file more readable and specify what each hash excludes:

```
# My Waiver File
# Comments can be used by starting the line with a '#'
36905f88444d24d110bb319d9469fa2a
7a176aa0bf1b1a2574d5214cc1e3cf1b # Comments can also be placed after a hash
```

The waiver hash is calculated from a number of properties:
 * The DesignFormat node that the violation was raised from;
 * The name of the checker that raised the violation;
 * The exact message included in the violation.

If the node is changed, or the name of the check changes, or the message that the check includes within the violation changes then the waiver will be invalidated and the violation will be raised to an error once again.

```eval_rst
.. note::
    Not all properties of the DesignFormat node are included within the hash. Specifically any values stored within the 'attributes' dictionary are ignored, this is because absolute paths may appear within the values and these will change between different systems and different users.
```

## Creating New Checks
Two types are defined for flagging rule violations:

 * `RuleViolation` - is a 'recoverable' violation, that is one that doesn't prevent further checks taking place. For example it might be used to flag that a particular register is not accessible through a parent address map aperture.
 * `CriticalRuleViolation`- is an 'unrecoverable' violation, that is one that prevents further analysis from taking place. For example it might be that the project appears corrupted, and cannot be analysed.

The two types of violation should be used in different ways - `RuleViolations` should be returned in a list at the end of the check, whilst `CriticalRuleViolations` should be treated as exceptions and should be raised as soon as they are detected (e.g. `raise CriticalRuleViolation(...)`).

Both types of violation can carry a message and a node - the node should be set equal to whatever DesignFormat object is the root cause of the violation (if known).

Rules should be stored under `blade/checkers` as their own Python file. At runtime, the checker framework will import all Python files it discovers under this path and register any functions beginning with `check_`. The function should take a single argument of the DFProject and return a list of `RuleViolations` - for example:

```python
def check_unique_names(project: DFProject):
    # Create an array to capture violations
    violations = []

    # Pickup all root nodes
    roots = project.getAllPrincipalNodes()

    # Raise a critical violation if the project is empty
    if len(roots) == 0:
        raise CriticalRuleViolation("Project is empty!", node=project)

    # Otherwise check that no two names of root nodes are the same
    found = []
    for obj in roots:
        if obj.id.strip().lower() in found:
            violations.append(RuleViolation(
                f"Duplicate name detected: {obj.id}", node=obj
            ))
        else:
            found.append(obj.id.strip().lower())

    # Return the list of violations
    return violations
```

## API

```eval_rst
.. automodule:: blade.checker
    :members:
    :undoc-members:
```

```eval_rst
.. automodule:: blade.checkers.common
    :members:
    :undoc-members:
```