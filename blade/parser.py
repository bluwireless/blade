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

import inspect
import os
import yaml

# Attempt to use the libYAML loader, fall back to normal loader if not available
try:
    from yaml import CLoader as Loader
except:
    print("WARNING: Falling back to pure Python YAML parser, will be slow")
    from yaml import Loader

class PhhidleParseError(Exception):
    """Custom Exception type that allows YAML parsing errors to be reported"""

    def __init__(self, message, path=None):
        """Initialise the validation error.

        Args:
            message: The exception message
            path   : Path to the YAML file being parsed
        """
        super().__init__(message)
        self.path = path

# Perform some magic to create a mapping between YAML tag and schema classes
from . import schema
schema_classes = {}
for schema_class in [x for x in inspect.getmembers(schema, inspect.isclass)]:
    if hasattr(schema_class[1], 'yaml_tag'):
        schema_classes[schema_class[1].yaml_tag] = schema_class[1]

def schema_constructor(loader, node, deep=True):
    """Custom tag constructor for building mapping or sequence nodes.

    Custom tag constructor that can either build mapping nodes or sequence nodes
    depending on the input. This automatically allows any schema class to support
    both methods of declaration. This constructor also performs a basic validation
    that all required keys are presented, and no unsupported keys are present.

    Args:
        loader: The PyYAML loader instance
        node  : The current YAML node to digest
        deep  : Whether to perform deep population of the node

    Returns:
        TagBase: The parsed YAML tag as a Python object
    """
    required = optional = []

    # Extract all mandatory and optional variables
    if node.tag in schema_classes:
        argspec  = inspect.getargspec(schema_classes[node.tag].__init__)
        args     = argspec.args if argspec.args != None else []
        defaults = argspec.defaults if argspec.defaults != None else []
        # NOTE: We always ignore zeroeth argument as it is the 'self' reference
        required = args[1:(len(args) - len(defaults))]
        optional = args[(len(args) - len(defaults)):]

    # Perform mapping node construction
    if isinstance(node, yaml.MappingNode):
        if node.tag in schema_classes:
            mapping = {}
            for key_node, value_node in node.value:
                key   = loader.construct_object(key_node,   deep=deep)
                value = loader.construct_object(value_node, deep=deep)
                if key in mapping:
                    raise yaml.constructor.ConstructorError(
                        f"Duplicate key {key}",
                        node.start_mark,
                        f"Duplicate key {key} when constructing node {node.tag}",
                        value_node.start_mark
                    )
                mapping[key] = value
            # Perform check that we have everything we need and nothing we don't!
            missing = [x for x in required if x not in mapping]
            excess  = [x for x in mapping.keys() if x not in required and x not in optional]
            if len(missing) > 0:
                raise yaml.constructor.ConstructorError(
                    None, node.start_mark,
                    f"Unable to construct {node.tag} due to missing keys: {', '.join(missing)}",
                    node.start_mark
                )
            if len(excess) > 0:
                raise yaml.constructor.ConstructorError(
                    None, node.start_mark,
                    f"Unable to construct {node.tag} due to unrecognised keys: {', '.join(excess)}",
                    node.start_mark
                )
            # Generate and return the schema object
            result = schema_classes[node.tag](**mapping)
            result.set_file_marks(node.start_mark, node.end_mark)
            return result
        else:
            raise yaml.constructor.ConstructorError(
                None, node.start_mark,
                f"Could not find schema class for tag {node.tag} when constructing mapping node",
                node.start_mark
            )

    # Perform sequence node construction
    elif isinstance(node, yaml.SequenceNode):
        if node.tag in schema_classes:
            seq = loader.construct_sequence(node)
            # Perform check that we have everything we need and nothing we don't!
            num_got = len(seq)
            num_req = len(required)
            num_all = (num_req + len(optional))
            if num_got < num_req:
                raise yaml.constructor.ConstructorError(
                    None, node.start_mark,
                    f"Unable to construct {node.tag} only have {num_got} items and need {num_req}",
                    node.start_mark
                )
            if num_got > num_all:
                raise yaml.constructor.ConstructorError(
                    None, node.start_mark,
                    f"Unable to construct {node.tag} only need {num_all} items and have {num_got}",
                    node.start_mark
                )
            # Extract all mandatory and optional variables
            result = schema_classes[node.tag](*seq)
            result.set_file_marks(node.start_mark, node.end_mark)
            return result
        else:
            raise yaml.constructor.ConstructorError(
                None, node.start_mark,
                f"Could not find schema class for tag {node.tag} when constructing sequence node",
                node.start_mark
            )

    # Unrecognised node type
    else:
        raise ValueError("Unknown node type: " + type(node))

# Register the custom constructor for every YAML tag we support in the schema
for key in (x for x in schema_classes.keys() if x != None):
    yaml.add_constructor(
        schema_classes[key].yaml_tag, schema_constructor, Loader=Loader
    )

def parse_phhidle_file(path, prefile=None, buffer=None):
    """Parse a Phhidle schema YAML file for all documents that are described.

    Args:
        path   : The path to the YAML file
        prefile: The PreprocessorFile object (used to map line numbers, optional)
        buffer : The contents of the YAML file (allow this to be either directly
                 from the file, or post-preprocessor). This is optional, if not
                 provided then the file will be loaded from disk.

    Returns:
        list: Collection of documents parsed from the raw YAML input
    """
    # If no buffer is provided, load file from disk
    if buffer == None:
        if not os.path.exists(path) or os.path.isdir(path):
            raise Exception(f"Could not open file at path {path}")
        with open(path, 'r') as fh:
            buffer = fh.read()
    # If an array buffer is provided, convert it to a string
    elif isinstance(buffer, list):
        buffer = "\n".join([x.replace("\n", "") for x in buffer])
    # Once we have a buffer, push it through the YAML parser
    try:
        documents = yaml.load(buffer, Loader=Loader)
    except yaml.constructor.ConstructorError as e:
        bad_line = e.problem_mark.line
        bad_path = path
        if prefile != None:
            bad_line = prefile.get_input_line_number(e.problem_mark.line)
            bad_file = prefile.get_input_line_file(e.problem_mark.line)
            bad_path = bad_file.path if bad_file else "UNKNOWN FILE"
        raise PhhidleParseError(
            f"Caught construction error when handling {bad_path} line {bad_line+1} column "
            f"{e.problem_mark.column}: {e}", path=bad_path
        ) from e
    except yaml.parser.ParserError as e:
        bad_line = e.problem_mark.line
        bad_path = path
        if prefile != None:
            bad_line = prefile.get_input_line_number(e.problem_mark.line)
            bad_path = prefile.get_input_line_file(e.problem_mark.line).path
        raise PhhidleParseError(
            f"Caught parsing error when handling {bad_path} line {bad_line+1} column "
            f"{e.problem_mark.column}: {e}", path=bad_path
        ) from e
    return documents
