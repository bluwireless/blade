# BLADE

BLADE is a bespoke Blu Wireless tool for autogenerating modules, interconnects, and register definitions from a YAML schema. BLADE is a complete re-structuring and re-implementation of a tool developed early in Blu Wireless's timeline, which had grown organically over time and reached a point where it was difficult to add new features.

The original tool performed two roles - firstly it parsed and elaborated the YAML design, and secondly it drove a Mako-based templating engine to produce SystemC, Verilog, and other output formats. These two roles were not cleanly separated, with elaboration split between core code and templates - making it difficult to determine the exact rules by which the design was constructed.

BLADE is designed to only perform the first of the two roles - going from YAML through to a fully elaborated design, ready to be handed-off to another tool for further processing (for example a templating engine). The output from BLADE is a DesignFormat interchange file, which allows the fully elaborated design to be dumped into a JSON in such a way that the state can be reloaded with the hierarchy and interconnections all intact. By using an interchange format, the separation between the elaboration and templating phases can be guaranteed - and multiple tools can be driven with exactly the same information (for example BLADE Viewer). Javascript and Python libraries exist for manipulating DesignFormat, so it can easily integrated into new or existing tools.

# Contents
```eval_rst
.. Declare a real ToC so that we can navigate using the sidebar, but make it hidden so we can use the custom version above - which has descriptions for each item!
.. toctree::
   :maxdepth: 3

   sections/architecture.md
   sections/schema.md
   sections/cli.md
   sections/guides_examples.md
```

# Indices and tables

```eval_rst
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```
