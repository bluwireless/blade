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

import hashlib
import json
import os
import re
from timeit import default_timer as timer

# Get hold of the report
from . import reporting
report = reporting.get_report("checker")

# Import the different rule checkers
from .checkers import get_all_checkers
from .checkers.common import RuleViolation, CriticalRuleViolation

# Import DesignFormat project
from designformat import DFProject, DFBase

def violation_id(node: DFBase, project: DFProject, checker: str, message: str):
    """ Generate an identifier for a rule violation used in waiving errors.

    To allow certain rule violations to be waived, the checker generates a unique
    identifier for each case. A waiver file can then be provided that instructs
    the tool to lower the error level to just a warning.

    Args:
        node   : The node on which the violation has occurred.
        project: The top level DFProject containing the node.
        checker: Name of the checker raising the error.
        message: The violation message being waived.

    Returns:
        str: A unique identifier for the rule violation
    """
    # Dump the node that caused a violation into a dictionary
    dump = node.dumpObject(project)
    # Remove the 'attributes' array, as it can contain data that varies over time
    def rem_attrs(node):
        if type(node) in [map, dict]:
            if 'attributes' in node: del node['attributes']
            for child in node.values():
                rem_attrs(child)
        elif type(node) in [list]:
            for child in node:
                rem_attrs(child)
    rem_attrs(dump)
    # Convert the dump into JSON
    dump_str = json.dumps(dump)
    # If the node has a hierarchical path, use it
    node_id = node.hierarchicalPath() if hasattr(node, 'hierarchicalPath') else node.id
    # Concatenate the data and calculate a checksum
    return hashlib.md5(
        (type(node).__name__ + dump_str + node_id + message).encode()
    ).hexdigest()

def perform_checks(project: DFProject, waiver_files: list):
    """ Perform a number of checks on the elaborated design

    Rules can be defined to check that the design is sane, for example that all
    registers attached to a block are accessible through the aperture declared
    in the address map. Rules should not generally raise exceptions, unless a
    critical error is detected, instead they should capture a RuleViolation which
    will be logged. For a critical violation where the rest of the check would
    be invalid, the check should raise a CriticalRuleViolation. This approach
    allows the project to be saved to disk, but still captures any failures that
    have occurred.

    Args:
        project     : The DesignFormat project
        waiver_files: A list of paths to waiver files which can be used to
                      downgrade errors to warnings

    Returns:
        list: List of all RuleViolation objects returned by checkers
    """

    # First read in all of the waivers
    # NOTE: Waivers are hexadecimal MD5 hashes, comments designated by '#'
    waivers    = []
    rgx_waiver = re.compile(r"^([a-fA-F0-9]+)[\s]{0,}(?:$|#[\s]{0,}.*?$)")
    for path in waiver_files:
        if not os.path.exists(path):
            raise Exception(f"Could not open waiver file at path {path}")
        file_waivers = []
        with open(path, 'r') as fh:
            for line in fh.readlines():
                match = rgx_waiver.match(line)
                if not match: continue
                key = match.groups()[0].strip().lower()
                if len(key) > 0: file_waivers.append(key)
        waivers += file_waivers
        report.debug(f"Loaded {len(file_waivers)} waivers from {path}")

    # Run every check in the database
    violations = []
    checkers   = get_all_checkers()
    for check in checkers:
        check_name = check[0]
        check_func = check[1]
        assert callable(check_func)
        report.info(f"Executing check '{check_name}'")
        start = timer()
        try:
            # Execute the check - we expect it to return a list of RuleViolations
            result = check_func(project)
            assert (type(result) == list)
            # Check if any violations were raised
            if len(result) == 0:
                report.info(f"Check '{check_name}' succeeded")
            else:
                for v in result:
                    assert (type(v) == RuleViolation)
                    v_id = violation_id(v.node, project, check_name, v.message)
                    if v_id in waivers:
                        report.warning(
                            f"Waived violation '{v_id}' from {check_name} on "
                            f"node {type(v.node).__name__}::{v.node.id}",
                            body=v.message
                        )
                    else:
                        report.error(
                            f"{check_name} raised violation '{v_id}' on node "
                            f"{type(v.node).__name__}::{v.node.id}",
                            body=v.message
                        )
                        print(v.message)
                        violations.append(v)
        # Catch critical violations that terminate a checking routine
        except CriticalRuleViolation as e:
            v_id = violation_id(e.node, project, check_name, e.message)
            if v_id in waivers:
                report.warning(
                    f"Waived critical violation '{v_id}' from {check_name} on "
                    f"node {type(e.node).__name__}::{e.node.id}",
                    body=e.message
                )
            else:
                report.error(
                    f"{check_name} raised critical violation '{v_id}' on node "
                    f"{type(e.node).__name__}::{e.node.id}",
                    body=e.message
                )
                print(e.message)
                violations.append(e)
        report.info("Check '%s' took %0.02fs to complete" % (check_name, timer() - start))
    # Return all of the violations
    return violations



