# Command Line Interface

BLADE is provided with a comprehensive command line interface that will be sufficient for most needs. It will allow you to parse a design and generate a DesignFormat blob which you can then use to drive other tools such as code generators.

BLADE requires Python 3.6 or newer to operate, it also needs a checkout of DesignFormat available on your system - with the path to the root directory exported as `DESIGN_FORMAT_DIR`. DesignFormat is not distributed as part of BLADE as it is a standalone library.

You can access a quick description of BLADE and the options it takes by executing the following command:

```bash
$> export DESIGN_FORMAT_DIR=../design_format
$> python3.6 -m blade -h
usage: __main__.py [-h] [--include INCLUDE] --top TOP [--enable-convert]
                   [--define DEFINE] --output OUTPUT [--report]
                   [--report-path REPORT_PATH] [--dependencies] [--MT MT]
                   [--MF MF] [--shallow] [--run-checks]
                   [--waiver-file WAIVER_FILE] [--ignore-check-errors]
                   [--quiet] [--profile] [--debug]

Tool for elaborating the Phhidle YAML into DesignFormat

optional arguments:
  -h, --help                        show this help message and exit
  --include INCLUDE, -i INCLUDE     Include a files or folder
  --top TOP, -t TOP                 Path to the 'top' file to start elaborating from
  --define DEFINE, -D DEFINE        Define a value for the preprocessor phase. Optionally you can specify the value '--define MYVAR=123'.
  --output OUTPUT, -o OUTPUT        Output path to store the DFBlob or DFProject file.
  --report                          Enable HTML report generation after blob generation completes.
  --report-path REPORT_PATH         Specify the output path for the report.
  --dependencies                    Enable dependency file generation.
  --MT MT                           The Makefile target to generate a dependency list for.
  --MF MF                           Output path for Makefile dependency lists for generating this blob.
  --shallow, -s                     Run in shallow mode - generating DesignFormat blobs with short hierarchy
  --run-checks, -c                  Enable rule checking - will test project before saving it to file
  --waiver-file WAIVER_FILE, -w WAIVER_FILE     Provide waiver files to the checking stage, multiple files can be provided and all waivers considered
  --ignore-check-errors             If enabled, when rule checks fail they will not cause an error exit code
  --quiet, -q                       Run in quiet mode - suppressing status messages
  --profile, -p                     Enable profiling, measures the execution time of each phase
  --debug                           Enable debug messages, including tracebacks after exceptions are caught.
```

## Basic Usage
Say you want to generate a DesignFormat blob starting from your design's top-level `my_soc.yaml`. You also have module, register, and interconnect definitions spread across multiple directories that you need to include to fully generate the design. In this case you need to use something like the following syntax:

```bash
$> python3.6 -m blade -i /path/to/my/his -i /path/to/my/reg -i /path/to/my/mods -i /path/to/a/specific/mod.md -t /path/to/my/mods/my_soc.yaml -o ./output.df_blob
```

Working through this command:

 * `-i /path/to/my/...` adds a directory, or file, to the search path - allowing the preprocessor to resolve any `#include` directives that reference it.
 * `-t .../my_soc.yaml` specifies which file contains the top-level of the design. BLADE will identify the root module and elaborate the design tree recursively.
 * `-o ./output.df_blob` specifies the path where the output DesignFormat blob should be written to.

While this example uses a `!Mod` as its top-level, you can equally provide files containing `!His`, `!Reg`, `!Inst`, or `!Def` as the root nodes and the elaborator will adjust accordingly.

For top-levels that contain multiple documents, each tag will be separately elaborated and attached to a single DFProject. This can be especially useful when a file contains multiple nodes like `!Def`, allowing you to store all of your constants in one place.

## Enabling Reports
BLADE captures all of the debug, info, warning, and error messages raised as it runs and can write them out to file in a single page HTML report. By default this report is not generated, but you can easily switch it on:

```bash
$> python3.6 -m blade -i ... -t my_soc.yaml ... --report --report-path ./my_report.html
```

The important options here are:
 * `--report` switches on report generation. Log messages are always captured and printed on the command line, but won't normally be written out to a file - this option forces a report to be written out.
 * `--report-path` allows you to specify the path that the report will be written to. If you leave out this option then the report will be written to the default file of `report.html` in the current working directory.

## Generating Makefile Dependencies
BLADE can generate dependency files that can be included into Makefiles to reduce the recomputation necessary any time a file in your design changes.

```bash
$> python3.6 -m blade -i ... -t my_soc.yaml -o my_soc.df_blob --dependencies --MT my_soc.df_blob --MF my_soc.deps
```

The arguments largely use the same syntax as GCC:
 * `--dependencies` enables dependency computation and file generation, in accordance with the next two parameters.
 * `--MT my_soc.df_blob` specifies which Makefile target we want to generate dependencies for - this should normally match the name of your output blob file.
 * `--MF my_soc.deps` specifies the path where the dependency file should be written - here we're going to create `my_soc.deps` in the current working directory.

## Enabling Rule Checks
BLADE has an extensible engine for running [automated rule checks](./architecture/checker.md) against a fully elaborated design - although by default this feature is switched off. To enable it use the following command:

```bash
$> python3.6 -m blade ... --run-checks --waiver-file my.waivers --waiver-file ../freds.waivers
```

Here we've used some of the possible options:
 * `--run-checks` enables rule checking - without this the checking stage is bypassed silently.
 * `--waiver-file my.waivers` specifies a waiver file - you can have as many of these as you require, the syntax is detailed on the [checker's architecture page](./architecture/checker.md).

One other option not used above is `--ignore-check-errors` - this stops the tool exiting with an error code (exit code != 0) if any rule checks (critical or not) fail. This is **not** the default behaviour.

## Passing in Defined Values
When the preprocessor executes, it will replace any values that it is aware of with constants defined in the scope. There are three ways to define a constant:

 * You can use a `#define MY_KEY 2` declaration within your source code;
 * You can export a value into your environment before executing BLADE (e.g. `export MY_KEY=2`);
 * Or, you can define a value on the command line using `--define MY_VAL=2`.

```bash
$> python3.6 -m blade ... --define MY_KEY_W_VAL=3 --define JUST_A_KEY
```

As shown above you can optionally provide a value to a defined key by using the syntax `--define <KEY>=<VAL>`. If you do not provide a value, then it will be given a boolean `True` value by default.

## Limiting the Elaboration Depth
By default BLADE will recursively elaborate the design until it is fully resolved. However, you can limit the depth of the recursion by using the `--shallow` option. This will restrict `!Mod` elaboration to just one level - or in other words it will fully elaborate the parent module, but will only calculate the boundary IO for any child modules.

```bash
$> python3.6 -m blade -i ... -t top.yaml --shallow
```

This is especially useful when you want to produce small blobs for driving autogeneration, rather than caring about the fully elaborated design.

```eval_rst
.. note:
    Using `--shallow` will not alter the result of the elaboration, except for truncating the hierarchy. It is perfectly acceptable to rely on a shallow blob for generating boundary IO, connectivity, and the register set for a block.
```
