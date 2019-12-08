![BLADE](documentation/source/_static/images/BLADE.png)

---

BLADE is a tool for generating hierarchical hardware designs from a YAML based input syntax. It allows front-end designers to work like IP integrators from day one, with the ability to describe blocks, interconnections, register and address maps and more with strict type checking and high-level design rule checks.

When BLADE executes, it produces a DesignFormat blob describing the hardware - this interchange format, which is based on JSON, can drive templating engines, GUIs, CLIs and more. The whole process is agnostic of the design implementation language used, so templates can be easily crafted to work with development flows in SystemC, Verilog, VHDL, and more.

# Simple Example
The example below demonstrates how a module can be declared with ports and children, and how an explicit connection can be described between two child nodes. Further details on using BLADE can be found in the documentation and example designs.

```yaml
#include "axi4_lite.yaml"
#include "wire.yaml"

#include "watchdog_ctrl.yaml"
#include "watchdog_tmr.yaml"

- !Mod
  name       : watchdog
  ld         : A four channel watchdog timer
  ports      :
  - !HisRef [cfg, axi4_lite, "Configuration port", 1, slave ]
  - !HisRef [irq, wire,      "Interrupt outputs",  4, master]
  modules    :
  - !ModInst [ctrl,  watchdog_ctrl, "Control block for the timers", 1]
  - !ModInst [timer, watchdog_tmr,  "Timer modules",                4]
  connections:
  - !Connect
    points:
    - !Point [timer_enable, ctrl ]
    - !Point [enable,       timer]
  ...
```

# Getting Started with BLADE

## System Requirements
BLADE is a Python based tool, and has a few system dependencies:
 * Python 3.6 or greater
 * [PyYAML](https://pypi.org/project/PyYAML/) - Used to power the YAML parser
 * [Mako](https://pypi.org/project/Mako/) - Templating engine used for generating reports, also used by the BLADE Templating Engine
 * [TQDM](https://pypi.org/project/tqdm/) - CLI compatible progress bars
 * [DesignFormat](https://github.com/bluwireless/designformat) - The interchange format used by BLADE

```bash
$> pip install pyyaml mako tqdm
$> pip install git+https://github.com/bluwireless/designformat#subdirectory=python
```

As BLADE designs can get quite big, we recommend using PyYAML's CLoader which uses LibYAML to accelerate the parsing process - it can result in some quite substantial speed ups when generating large designs. [More details can be found here](https://pyyaml.org/wiki/PyYAMLDocumentation).

The following dependencies are not mandatory, but are required for building the documentation:
 * [Sphinx](https://pypi.org/project/Sphinx/) - Powerful documentation generation tool
 * [Recommonmark](https://pypi.org/project/recommonmark/) - Markdown convertor for Sphinx
 * [Sphinx Markdown Tables](https://pypi.org/project/sphinx-markdown-tables/) - Markdown table convertor for Sphinx
 * [Sphinx RTD Theme](https://pypi.org/project/sphinx-rtd-theme/) - Read The Docs theme for Sphinx HTML

```bash
$> pip install sphinx recommonmark sphinx-markdown-tables sphinx-rtd-theme
```

## Building Your First Design

## Next Steps