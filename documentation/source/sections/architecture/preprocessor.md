# Preprocessor
To assist with generation of a complex IP, a preprocessing language is available that utilises the comment delimeter (`#`) within the YAML source data. The preprocessing stage must be completed before the YAML parse can take place - otherwise the state of the design will not be fully resolved, and the result will be invalid. A number of different macros exist, all operating in a detached namespace from the YAML parser - i.e. values declared within the preprocessing markup are not available by default to the YAML parser and vice-versa.

The preprocessor is implemented using a 'lazy' load and evaluation strategy - this means that files are only loaded into memory and evaluated at the point they are required. The preprocessor can be told about as many files as required, but it will ignore any files that are not referenced by an `#include` macro.

While BLADE heavily relies on the preprocessor, it is general purpose and can be used by other tools via its API. This is described below, along with an example of how to instantiate and run it.

Further details on the components used by the preprocessor during evaluation can be found on a separate page [Preprocessor Components](preprocessor_components.md).

## Syntax
The following section describes the syntax of the preprocessor. Each of these directives can be used to control the output to the parsing stage of the workflow.

### #define
Defines a value in the preprocessor's scope that can be used for comparisons, arithmetic, or printed out into the body of the text. Note that `#define`'d values can reference other values.

#### Example
```
#define VAL_1 3
#define VAL_2 5
#define VAL_3 (VAL_1 * VAL_2)
VAL 1 = <VAL_1>
VAL 2 = <VAL_2>
VAL 3 = VAL 1 * VAL 2 = <VAL_3>
```

#### Result
```
VAL 1 = 3
VAL 2 = 5
VAL 3 = VAL 1 * VAL 2 = 15
```

**NOTE**

```eval_rst
.. note::
    The syntax expected when expanding the value of any macro is Python 3 compliant, this means using:
     * `*`, `+`, `-` for multiplication, addition, and subtraction;
     * `//` for integer division, `/` for floating point division (however `/` is currently replaced by `//` for backwards compatibility);
     * `**` for raising a value to a power;
     * `<<` and `>>` for shift operations;
     * `and` and `or` for boolean comparisons.
```

### #include
This macro includes the text of another file into the body of the parent file, at the position of the `#include` macro. It also makes the preprocessor aware of any values that are `#define`'d within the included file.

#### Example
file_1.yaml:
```
#define MY_VAL 123
This is file 1
```

file_2.yaml:
```
This is the start of file 2
#include "file_1.yaml"
This is the value of MY VAL=<MY_VAL>
This is the end of file 2
```

#### Result
```
This is the start of file 2
This is file 1
This is the value of MY VAL=123
This is the end of file 2
```

### #if / #elif / #else / #endif and #ifdef / #ifndef
These macros allow for blocks of text to be conditionally included or excluded from the final result. Any expression may be used with the statement, provided that it is compliant with Python 3 syntax and can be evaluated to a boolean value.

Note that as the file is evaluated top-to-bottom, values that are `#define`'d within a `#if/#elif/#else/#endif` statement will only take effect for lines of code after the declaration.

#### Example
```
#define VAL_1 1
#define VAL_2 VAL_1 * 50
#if VAL_2 < 25
    #define VAL_3 123
    #define VAL_4 128
#elif (VAL_1 != 100) and (VAL_2 > 50)
    #define VAL_4 256
#endif
#ifndef VAL_3
VAL 3 was not defined
#endif
#ifdef VAL_4
VAL 4=<VAL_4>
#endif
```

#### Result
```
VAL 3 was not defined
VAL 4=256
```

### #for / #endfor
Where a block of code needs to be repeated multiple times, a `#for / #endfor` block can be used. As with `#if / ... / #endif` blocks, the expression may be any iterable compliant with Python 3.

The iteration variable is exposed to the block within the `#for / #endfor` state in the form of `$(x)` where `x` is the variable name. You may also perform basic arithmetic where the iteration variable is used, as shown in the example below.

#### Example
```
#define MAX_VAL 5
#for my_iter_val in range(MAX_VAL)
My value is $(my_iter_val) add $(my_iter_val+1) double $(my_iter_val*2)
#endfor

#for name in ["Dave","Bob","Anna","Kerry"]:
My name is $(name)
#endfor
```

#### Result
```
My value is 0 add 1 double 0
My value is 1 add 2 double 2
My value is 2 add 3 double 4
My value is 3 add 4 double 6
My value is 4 add 5 double 8

My name is Dave
My name is Bob
My name is Anna
My name is Kerry
```

```eval_rst
.. note::
    The iteration variable is exposed to the block inside the `#for / #endfor` statements, it can be accessed by `$(x)` where `x` is the variable name.
```

#### Value Substitution
The preprocessor attempts to perform text substitutions for all values that are declared using a `#define`. Values can either be listed directly, or enclosed within angle brackets (`<...>`) to make it clear that they are going to be substituted.

#### Example
```
#define MY_VAL 123
#define YOUR_VAL MY_VAL * 2
MY VAL=MY_VAL
YOUR VAL=<YOUR_VAL>
```

#### Result
```
MY VAL=123
YOUR VAL=246
```

## Usage
The preprocessor is used as part of BLADE, but it can also be used standalone to process files using the same preprocessing syntax. The example below shows how to instantiate the preprocessor, create a scope, attach a number of files, and then how to run the evaluation.

```python
from blade.preprocessor import Preprocessor

pre = Preprocessor()

# Create a scope called 'main' and provide a number of pre-defined values
pre.add_scope("main", defines={ "MY_VAL": 123, "MY_BOOL": False, "MY_STR": "Hey" })

# Add a number of files into the scope
# NOTE: No two files added to the same scope may have the same name, otherwise
#       they will clash (i.e. can't have 'a/file_1.yaml' and 'b/file_1.yaml').
pre.add_file("main", "/path/to/my/file_1.yaml")
pre.add_file("main", "/path/to/my/file_2.yaml")
pre.add_file("main", "/path/to/my/other/file_3.yaml")
pre.add_file("main", "/path/to/different/file_4.yaml")

# Retrieve a particular file from the scope
top = pre.get_scope("main").get_file("file_1.yaml")
top.evaluate()

# Write out the evaluated result to a file
with open("output.yaml", "w") as fh:
    fh.write(top.get_result())
```

## API
```eval_rst
.. automodule:: blade.preprocessor
    :members:
    :undoc-members:
```