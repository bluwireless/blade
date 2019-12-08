# Copyright (C) 2019 Blu Wireless Ltd.
# All Rights Reserved.
#
# This file is part of BLADE.
#
# BLADE is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# BLADE is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# BLADE.  If not, see <https://www.gnu.org/licenses/>.
#

import argparse
import json
import logging
import os
import sys
from timeit import default_timer as timer
import traceback

# Import BLADE dependencies
from blade.project import build_project
from blade.preprocessor.common import PreprocessorError
from blade.schema import ValidationError
from blade.parser import PhhidleParseError
from blade.elaborate.common import ElaborationError

# Get a handle on the report object
from blade.reporting import get_report, ReportCommon
report = get_report()

# ==============================================================================
# Main Entrypoint
# ==============================================================================
def main():
    # Capture the entry time
    entry = timer()

    # Setup the supported command line options
    parser = argparse.ArgumentParser(
        description="Tool for elaborating a design documented using the YAML "
        "schema into a DesignFormat project"
    )
    # - Input scope and file arguments
    parser.add_argument(
        "--include", "-i", action="append",
        help="Include a files or folder"
    )
    parser.add_argument(
        "--top", "-t", required=True,
        help="Path to the 'top' file to start elaborating from"
    )
    # - Input modifiers
    parser.add_argument(
        "--define", "-D", action="append", default=[],
        help="Define a value for the preprocessor phase. Optionally you can specify the value '--define MYVAR=123'."
    )
    # - Output file arguments
    parser.add_argument(
        "--output", "-o", required=True,
        help="Output path to store the DFBlob or DFProject file."
    )
    parser.add_argument(
        "--report", action="store_true", default=False,
        help="Enable HTML report generation after blob generation completes."
    )
    parser.add_argument(
        "--report-path", default="report.html",
        help="Specify the output path for the report."
    )
    parser.add_argument(
        "--dependencies", action="store_true", default=False,
        help="Enable dependency file generation."
    )
    parser.add_argument(
        "--MT",
        help="The Makefile target to generate a dependency list for."
    )
    parser.add_argument(
        "--MF",
        help="Output path for Makefile dependency lists for generating this blob."
    )
    # - Elaboration behaviour arguments
    parser.add_argument(
        "--shallow", "-s", action="store_true",
        help="Run in shallow mode - generating DesignFormat blobs with short hierarchy"
    )
    # - Rule checker behaviour arguments
    parser.add_argument(
        "--run-checks", "-c", action="store_true",
        help="Enable rule checking - will test project before saving it to file"
    )
    parser.add_argument(
        "--waiver-file", "-w", action="append", default=[],
        help="Provide waiver files to the checking stage, multiple files can be provided and all waivers considered"
    )
    parser.add_argument(
        "--ignore-check-errors", action="store_true", default=False,
        help="If enabled, when rule checks fail they will not cause an error exit code"
    )
    # - Miscellaneous arguments
    parser.add_argument(
        "--quiet", "-q", action="store_true", default=False,
        help="Run in quiet mode - suppressing status messages"
    )
    parser.add_argument(
        "--profile", "-p", action="store_true", default=False,
        help="Enable profiling, measures the execution time of each phase"
    )
    parser.add_argument(
        "--debug", action="store_true", default=False,
        help="Enable debug messages, including tracebacks after exceptions are caught."
    )

    # Parse the provided command line options
    args = parser.parse_args()

    # If debug is enabled, immediately wind up the verbosity
    if args.debug: report.verbosity = ReportCommon.DEBUG

    # Check if the report location is viable
    if args.report:
        if not os.path.isdir(os.path.dirname(os.path.abspath(args.report_path))):
            report.error(f"Report output directory does not exist: {args.report_path}")
            sys.exit(-1)
        elif os.path.isdir(os.path.abspath(args.report_path)):
            report.error(f"Report output path is a directory: {args.report_path}")
            sys.exit(-1)

    # Pickup the various arguments
    include_list = args.include if isinstance(args.include, list) else []
    top_file     = args.top
    out_file     = args.output

    # Ensure the include list is unique
    include_list = set(list([os.path.abspath(x) for x in include_list]))

    # Determine the depth we're working to (None -> infinite depth elaboration)
    depth = 1 if args.shallow else None

    # Parse out the options
    defines = {}
    for keyval in args.define:
        parts = keyval.strip().split('=')
        defines[parts[0]] = parts[1] if len(parts) > 1 else True

    # Trigger the parser
    df_blob    = None
    yaml_deps  = [] if args.MF != None else None
    error_code = 0
    try:
        (df_blob, violations) = build_project(
            top_file   = top_file,            # Path to file to elaborate from
            includes   = include_list,        # File and folder paths to include
            defines    = defines,             # Defined valued passed to the preprocessor phase
            max_depth  = depth,               # Maximum depth to elaborate to
            run_checks = args.run_checks,     # Enable rule checking of the DF project
            waivers    = args.waiver_file,    # Provide waiver files for rule checks
            quiet      = args.quiet,          # Run in quiet mode
            deps       = yaml_deps,           # Optionally capture YAML dependencies of blob
            profile    = args.profile,        # Enable time profiling
        )
        if violations and len(violations) > 0:
            report.error(f"BLADE detected {len(violations)} rule violation{'s' if len(violations) > 1 else ''}")
            error_code = 0 if args.ignore_check_errors else 6
    except PreprocessorError as e:
        report.error(f"Preprocessor stage failed: {e}", body=traceback.format_exc())
        if args.debug: print(traceback.format_exc())
        error_code = 1
    except PhhidleParseError as e:
        report.error(f"Parse stage failed: {e}", body=traceback.format_exc())
        if args.debug: print(traceback.format_exc())
        error_code = 1
    except ValidationError as e:
        report.error(f"Validation failed for parameter {e.parameter}: {e}", body=traceback.format_exc())
        if e.doc != None:
            report.error(f"Document !{type(e.doc).__name__}::{e.doc.name} {e.doc.print_source()}")
        if args.debug: print(traceback.format_exc())
        error_code = 2
    except ElaborationError as e:
        report.error(f"Elaboration Error: {e}", body=traceback.format_exc())
        if e.ph_doc != None:
            report.error(f"Document !{type(e.ph_doc).__name__}::{e.ph_doc.name} {e.ph_doc.print_source()}")
        if args.debug: print(traceback.format_exc())
        error_code = 4
    except Exception as e:
        report.error(f"Unexpected failure occurred in BLADE {top_file}: {e}", body=traceback.format_exc())
        if args.debug: print(traceback.format_exc())
        error_code = 5

    # Always write out a report if enabled (used for debug)
    if args.report:
        report.write_report(
            args.report_path,
            verbosity=(ReportCommon.DEBUG if args.debug else ReportCommon.INFO)
        )

    # Write this object out to file
    if df_blob != None:
        json_dump = json.dumps(df_blob.dumpObject())
        with open(out_file, 'w') as fh:
            fh.write(json_dump)
        if args.dependencies and args.MF:
            with open(args.MF, 'w') as fh:
                fh.write(f"{args.MT}: {' '.join(yaml_deps)}")
    # If a blob didn't generate and no error was raised, write out an empty file
    elif error_code == 0:
        with open(out_file, 'w') as fh:
            fh.write('{}')

    # Capture the delta between entry and exit time
    if args.profile:
        delta = (timer() - entry)
        print("PROFILING: Total execution time %0.02fs" % delta)

    # If we failed, bail out with the correct exit code
    if error_code != 0: sys.exit(error_code)

# Handle being called direct from the command line
if __name__ == "__main__":
    main()
