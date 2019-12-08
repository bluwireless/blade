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

import datetime
import os
from pathlib import Path
import sys
from timeit import default_timer as timer
from yaml.error import Mark

# Import TQDM for progress bars
from tqdm import tqdm
tqdm_opts = { "ncols": 50, "bar_format": "{l_bar}{bar}|" }

# Get report for this level
from . import reporting
report = reporting.get_report("project")

# Import parsing pipeline
from .preprocessor import Preprocessor, PreprocessorFile
from .parser import parse_phhidle_file
from .elaborator import elaborate
from .elaborate.common import ElaboratorScope
from .checker import perform_checks

from .schema import Def, Define, Mod, His, Reg, Port, Config, Group, ValidationError
from designformat import DFProject

def iterate(iterable, quiet=False, **tqdm_args):
    """ Wrap an iterable with TQDM if quiet mode disabled.

    Args:
        iterable : The iterable (array, set, etc) to wrap
        quiet    : Whether we are running quietly (default: False)
        tqdm_args: Arguments to TQDM
    #
    """
    return iterable if quiet else tqdm(iterable, **tqdm_args, **tqdm_opts)

def delta(start):
    """Measure the delta between start and the current time

    Args:
        start: The point to measure the delta from

    Returns:
        str: Formatted delta in seconds to two decimal places.
    """
    return "%0.02fs" % (timer() - start)

def build_project(
    top_file, includes=None, defines=None, max_depth=None, run_checks=False,
    waivers=None, quiet=False, deps=None, profile=False
):
    """ Parse and elaborate the YAML description into a DesignFormat project.

    Drive the pipeline of operations to go from raw Phhidle YAML files through to
    an elaborated design returned as a DFProject object. This can either perform
    a deep elaboration, where all layers of the hierarchy are expanded and all
    interconnections are resolved, or a shallow elaboration where only a limited
    number of layers are expanded.

    Args:
        top_file  : The top module declaration file begin elaborating from
        includes  : A list of files or folders to include (optional)
        defines   : Defined values to pass to different phases (optional)
        max_depth : The maximum depth to elaborate to (optional, by default
                  : performs a full depth elaboration - max_depth=None)
        run_checks: Enable rule checkers (default: False)
        waivers   : List of waiver files to provide to the checking stage
        quiet     : Disable status messages and progress bars (default: False)
        deps      : An array can be provided to store the list of YAML files that
                  : the top object depends on.
        profile   : Measure and print execution times of each phase (default: False)

    Returns:
        tuple: The generated DesignFormat project and a list of rule violations.
    """

    # Default arguments
    # NOTE: We don't put lists or maps as default arguments otherwise they become
    #       shared between all calls of 'build_project' (dangerous!)
    includes = includes if includes != None else []
    defines  = defines  if defines  != None else {}
    waivers  = waivers  if waivers  != None else []

    pre = Preprocessor()

    # Add some debug information to the report
    report.debug("BLADE instance        : " + os.path.abspath(os.path.realpath(__file__)))
    report.debug("Execution date & time : " + datetime.datetime.now().isoformat())
    report.debug("Execution user account: " + os.environ['USER'])

    # ==========================================================================
    # Stage 1: Build the full preprocessor scope required for elaboration
    # ==========================================================================

    # List out all of the includes
    report.info(f"Top file: {top_file}")
    report.info(f"Including {len(includes)} files and directories", body="\n".join(includes))

    start = timer()

    # Build a single scope to include all files, passing the list of defines
    pre.add_scope("main", defines=defines)
    for item in iterate(includes, quiet=quiet, desc="Building Scope"):
        if not os.path.exists(item):
            raise Exception(report.error(
                "build_scope", f"Could not locate included path: {item}"
            ))
        else:
            for item in Path(item).rglob('*.yaml'): pre.add_file("main", item)

    # Just in case the top-level module hasn't been hit by the include list
    if not pre.get_scope("main").get_file(top_file):
        pre.add_file("main", top_file)

    if profile:
        report.debug("profiling", f"Stage 1: Building scope took {delta(start)}")

    # ==========================================================================
    # Stage 2: Run the preprocessor from the top-level module, this will also
    #          handle any dependent files that were #include'd
    # ==========================================================================

    start = timer()

    pre_top = pre.get_scope("main").get_file(top_file)
    pre_top.evaluate()

    if profile:
        report.debug("profiling", f"Stage 2: Preprocessor evaluation took {delta(start)}")

    report.info(f"{len(pre.all_files)} files in preprocessor scope", body="\n".join([x.path for x in pre.all_files]))

    # ==========================================================================
    # Stage 3: For every file handled by the preprocessor, it is now passed into
    #          the YAML parser. Every document generated by the parser is then
    #          linked back to the preprocessed source file so it can be tracked.
    # ==========================================================================

    start = timer()

    # Parse all Phhidle documents from the preprocessed top level file
    parsed_docs = parse_phhidle_file(pre_top.path, prefile=pre_top, buffer=pre_top.get_result())

    # If no work to do, bail out early
    if not parsed_docs or len(parsed_docs) == 0:
        report.warning("parsing", f"No root documents detected in {top_file}")
        return (None, [])

    def rebuild_mark(mark):
        return Mark(
            mark.name, mark.index,
            pre_top.get_result()[mark.line-1].input_line,
            mark.column, mark.buffer, mark.pointer
        )

    # Now work through all documents, associating them to their source file. We
    # also eliminate any duplicate documents due to the same file being #include'd
    # multiple times
    bypass_types  = [Define]
    unique_docs   = []
    declared_docs = {}
    for doc in parsed_docs:
        type_key    = type(doc).__name__
        source_file = pre_top.get_input_line_file(doc.start_mark.line)
        # Check for this exact document being seen before (clashing #includes)
        if (
            (source_file.path in declared_docs                            ) and
            (type_key         in declared_docs[source_file.path]          ) and
            (doc.name         in declared_docs[source_file.path][type_key]) and
            # Some tags may be declared multiple times with the same name
            (type(doc)    not in bypass_types                             )
        ):
            doc = declared_docs[source_file.path][type_key][doc.name]
        # Otherwise this document is new
        else:
            # Keep track of this document (ignoring bypassed types)
            if type(doc) not in bypass_types:
                if not source_file.path in declared_docs:
                    declared_docs[source_file.path] = {}
                if not type_key in declared_docs[source_file.path]:
                    declared_docs[source_file.path][type_key] = {}
                declared_docs[source_file.path][type_key][doc.name] = doc
            # Include in the list of unique documents to use in elaboration
            unique_docs.append(doc)
            # Adjust the file and line that this document came from
            doc.set_source_file(source_file)
            doc.set_file_marks(rebuild_mark(doc.start_mark), rebuild_mark(doc.end_mark))
        # Link parsed document to the preprocessor result
        source_file.add_parsed_document(doc)

    if profile:
        report.debug("profiling", f"Stage 3: YAML parse took {delta(start)}")

    # ==========================================================================
    # Stage 4: Provide intrinsic definitions of the 'clock' and 'reset' His, and
    #          make sure that every scope has reference to them.
    # ==========================================================================

    start = timer()

    # Add a scope to the preprocessor, and make all other scopes dependent
    # NOTE: To allow some templates to work, we need to make this look as if the
    #       declaration comes from within `interface_definitions`
    intrinsic_key   = "__intrinsics__"
    intrinsic_docs  = []
    intrinsic_scope = pre.add_scope(intrinsic_key, [])
    for scope_key in (x for x in pre.scopes if x != intrinsic_key):
        pre.scopes[scope_key].add_dependency(intrinsic_key)

    # Add clock defintion to the intrinsic types
    his_clock = His(
        "clock", [Port("clk", 1)],
        options  = ["BOOL", "signal_type=bwt_sc_immediate_clk"],
        includes = ["bwt_sc_immediate_clk.hpp"]
    )
    intrinsic_clk = pre.add_file(
        intrinsic_key,
        "interface_definitions/dev/view/yaml_his/intrinsic_clock.yaml",
        evaluated=True
    )
    intrinsic_clk.add_parsed_document(his_clock)
    his_clock.set_source_file(intrinsic_clk)
    intrinsic_docs.append(his_clock)

    # Add reset definition to the intrinsic types
    his_reset = His("reset", [Port("rst", 1)], options=["BOOL"])
    intrinsic_rst = pre.add_file(
        intrinsic_key,
        "interface_definitions/dev/view/yaml_his/intrinsic_reset.yaml",
        evaluated=True
    )
    intrinsic_rst.add_parsed_document(his_reset)
    his_reset.set_source_file(intrinsic_rst)
    intrinsic_docs.append(his_reset)

    # Add the intrinsics as included by all other files
    for file in pre.get_all_evaluated_files():
        file.include_file("intrinsic_clock.yaml", bypass=True)
        file.include_file("intrinsic_reset.yaml", bypass=True)

    # Add the intrinsics to be validated
    all_documents = (unique_docs + intrinsic_docs)

    if profile:
        report.debug("profiling", f"Stage 4: Intrinsic construction took {delta(start)}")

    # ==========================================================================
    # Stage 5: Validation - we check that every parsed document adheres to the
    #          Phhidle schema. Each document contains a 'validate' routine. This
    #          stage also builds a map between document name and the document.
    # ==========================================================================

    start = timer()

    for doc in iterate(all_documents, quiet=quiet, desc="Schema Check  "):
        doc.validate()

    if profile:
        report.debug("profiling", f"Stage 5: Validation took {delta(start)}")

    # ==========================================================================
    # Stage 6: Elaboration - expand the definition of the top module depending
    #          on the type.
    # ==========================================================================

    start = timer()

    # Find all documents defined directly in the top document
    top_docs = pre_top.get_parsed_documents()

    # Find all documents included by the top file (including chain)
    inc_docs = [x for x in unique_docs if x not in top_docs]

    # Populate the 'deps' array with dependencies
    if deps != None:
        # NOTE: Don't include intrinsics as they don't really exist!
        dep_set = set([x.source.path for x in (top_docs + inc_docs) if x.source.scope != intrinsic_key])
        for dep in dep_set:
            deps.append(dep)

    # Build a scope object
    elab_scope = ElaboratorScope()
    for doc in all_documents:
        # Don't add unnamed documents to the scope, and avoid clashing with any
        # intrinsic types
        if doc.name and doc.name not in (x.name for x in intrinsic_docs):
            elab_scope.add_document(doc)

    # Add any intrinsic types
    for doc in intrinsic_docs:
        if doc.name:
            elab_scope.add_document(doc)

    # Elaborate all documents in the top file into a single DFProject
    project      = elaborate(top_docs, elab_scope, max_depth=max_depth)
    project.id   = os.path.splitext(os.path.split(top_file)[-1])[0]
    project.path = top_file

    if profile:
        report.debug("profiling", f"Stage 6: Elaboration took {delta(start)}")

    # ==========================================================================
    # Stage 7: Checking - perform checks on the elaborated design (optional).
    # ==========================================================================

    violations = []

    if run_checks:
        start = timer()

        violations = perform_checks(project, waivers)

        if profile:
            report.debug("profiling", f"Stage 7: Checking took {delta(start)}")

    return (project, violations)
