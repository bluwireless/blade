# Preprocessor: Components
The preprocessor uses a number of classes for tracking the state within the file whilst evaluating it. It monitors every line in the input file, separating them into blocks created by macros (such as `#for / #endfor` and `#if / #endif`), and including lines from other files where required by a `#include` macro. The API of each of these tracking classes is documented below.

## PreprocessorScope
```eval_rst
.. automodule:: blade.preprocessor.scope
    :members:
    :undoc-members:
```

## PreprocessorFile
```eval_rst
.. automodule:: blade.preprocessor.file
    :members:
    :undoc-members:
```

## PreprocessorBlock
```eval_rst
.. automodule:: blade.preprocessor.block
    :members:
    :undoc-members:
```

### PreprocessorForBlock
```eval_rst
.. automodule:: blade.preprocessor.for_block
    :members:
    :undoc-members:
```

### PreprocessorIfBlock
```eval_rst
.. automodule:: blade.preprocessor.if_block
    :members:
    :undoc-members:
```

## PreprocessorLine
```eval_rst
.. automodule:: blade.preprocessor.line
    :members:
    :undoc-members:
```

## PreprocessorStatement
```eval_rst
.. automodule:: blade.preprocessor.statement
    :members:
    :undoc-members:
```