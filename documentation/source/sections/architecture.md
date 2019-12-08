# Architecture
BLADE is a complex tool with a wide array of capabilities. To help users gain a more advanced understanding of the tool and how best to use it, the following documents describe the different stages of the workflow.

For users looking to gain an even deeper understanding, or for those wishing to extend the core functionality, we recommend looking into the source code - it is fairly thoroughly commented, and split into different modules for each stage of the workflow.

## Documentation
* [Project](./architecture/project.md) - explains the workflow, ƒrom taking input files and returning a DFProject.
* [Preprocessor](./architecture/preprocessor.md) - demonstrates the available preprocessing syntax and how it can be used to simplify your definitions.
* [Preprocessor Components](./architecture/preprocessor_components.md) - details handlers for each preprocessor command such as `#include` or `#if/elif/else`.
* [YAML Parser](./architecture/parser.md) - documents the input parser and how both sequence and mapping nodes are digested.
* [Tag Validation](./architecture/validation.md) - details the checks that are performed on input documents before being run through the elaborator.
* [Elaboration](./architecture/elaboration.md) - documents the different elaboration engines that are available and how they inter-operate to construct the final design.
* [Rule Checks](./architecture/checker.md) - explains the extensible framework for automated rule checks and waivers built into BLADE.

```eval_rst
.. Declare a real ToC so that we can navigate using the sidebar, but make it hidden so we can use the custom version above - which has descriptions for each item!
.. toctree::
   :maxdepth: 1
   :hidden:

   ./architecture/project.md
   ./architecture/preprocessor.md
   ./architecture/preprocessor_components.md
   ./architecture/parser.md
   ./architecture/validation.md
   ./architecture/elaboration.md
   ./architecture/checker.md
```