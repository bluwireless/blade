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

import os
import re

from .. import reporting
report = reporting.get_report("preprocessor.file")

from .block import PreprocessorBlock
from .common import PreprocessorError, preprocessor_regex
from .for_block import PreprocessorForBlock
from .if_block import PreprocessorIfBlock
from .line import PreprocessorLine
from .statement import PreprocessorStatement

class PreprocessorFile(object):
    """
    Represents a file that has been loaded for preprocessing, allows it to carry
    state such as what other files have been included, what values have been
    defined, etc. The preprocessor runs on a iterative basis, attempting to resolve
    files one at a time - this gets around the issue of '#include' and '#define'
    statements being made conditional on other variable defined in other files.
    """

    def __init__(self, path, scope, preprocessor, evaluated=False):
        """ Initialisation function for a file.

        Note that the file's contents are not immediately load in order to reduce
        file system and memory load. Once a file is needed, the evaluate function
        will automatically load the contents into memory.

        Args:
            path        : The absolute path to the file to load
            scope       : The scope for this file, including the other files
                          available within the repository, and any dependencies.
            preprocessor: The top-level preprocessor holding all files
            evaluated   : Mark file as evaluated, use for injecting programmatically
                          defined documents into the evaluation scope (default: False)
        """
        self.__path         = str(path)
        self.__scope        = scope
        self.__preprocessor = preprocessor
        # State variables
        self.__force_resolve = False     # Forces the evaluation process to finalise
        self.__evaluated     = evaluated # Has evaluation been completed
        self.__lines         = []        # Collecting of blocks, statements, and strings
        self.__parse_context = []        # The hierarchy down to the block being assembled
        self.__final         = []        # The result of the successful evaluation
        self.__includes      = []        # List of #include'd files
        # Extraneous variables
        self.__documents     = []        # Used to relate parsed documents back to source

    @property
    def path(self):
        """ Path to the file on disk """
        return self.__path

    @property
    def scope(self):
        """ PreprocessorScope instance that contains this file """
        return self.__scope

    @property
    def evaluated(self):
        """ Has this file been successfully evaluated? """
        return self.__evaluated

    @property
    def loaded(self):
        """ Has the file been loaded from disk? """
        return len(self.__lines) > 0

    def set_definition(self, key, value):
        """ Add a new key-value pair to the scope's definitions map.

        Args:
            key  : The key for the definition
            value: The value of the definition
        """
        self.__preprocessor.get_scope(self.__scope).set_definition(key, value)

    def list_all_defines(self):
        """ Return all of the values defined in the scope.

        Returns:
            map: Returns the map of defined values.
        """
        return self.__preprocessor.get_scope(self.__scope).defines

    def include_file(self, file, bypass=False):
        """ Add a new file to be included from the scope when evaluating this file.

        Args:
            file  : The file to include
            bypass: Bypass evaluation check, used to inject fake files (default: False)
        """
        file = file.strip()
        if len(file) > 0 and not file in self.__includes:
            self.__includes.append(file)
            # Check that the included file has been loaded and evaluated
            if not bypass:
                inc_file = self.__preprocessor.find_file(self.__scope, file)
                if not inc_file:
                    raise PreprocessorError(report.error(
                        f"Cannot resolve file {file} - included by {self.path}"
                    ), path=self.path)
                if not inc_file.evaluated:
                    inc_file.evaluate()

    def all_included_files(self, top=True, recursive=False):
        """ Return a list of all included PreprocessorFile's

        Args:
            top      : List the files that this one directly includes (default: True)
            recursive: List all files referenced by included files (default: False)
        """
        files = []
        for file in self.__includes:
            inc_file = self.__preprocessor.find_file(self.__scope, file)
            if inc_file:
                if top:
                    files.append(inc_file)
                if recursive:
                    files += inc_file.all_included_files()
        return files

    def get_result(self):
        """ Return the evaluated file contents

        Returns:
            list: List of output lines from evaluation as PreprocessorLine
                  instances
        """
        return self.__final

    def get_input_line_file(self, line_no):
        """ Maps from line in evaluated output to the input PreprocessorFile.

        Args:
            line_no: Line number within the evaluation output (indexed 0 upwards)

        Returns:
            PreprocessorFile: Returns the file responsible for a line in the output
        """
        if line_no < 0 or line_no >= len(self.__final):
            raise ValueError(report.error(
                f"Line number {line_no} is out of range (0 - {len(self.__final)-1})"
            ))
        # NOTE: Compensate for the fact we index lines from 0
        return self.__final[line_no].source_file

    def get_input_line_number(self, line_no):
        """ Maps from line in evaluated output to line number in the input file

        Args:
            line_no: Line number within the evaluation output (indexed 0 upwards)

        Returns:
            int: The line number within the input file
        """
        if line_no < 0 or line_no >= len(self.__final):
            raise ValueError(report.error(
                f"Line number {line_no} is out of range (0 - {len(self.__final)-1})"
            ))
        # NOTE: Compensate for the fact we index lines from 0
        return self.__final[line_no].input_line

    def get_current_context(self):
        """ Returns the current context of the parse (block most recently assembled).

        Returns:
            PreprocessorBlock: The block if within a context, otherwise None
        """
        if len(self.__parse_context) > 0:
            return self.__parse_context[-1]
        else:
            return None

    def push_to_current_context(self, item):
        """ Add a new item to the current context

        This can be a PreprocessorBlock, PreprocessorStatement, or a basic
        PreprocessorLine. If a block is pushed it will *not* be pushed onto the
        context stack, instead you should use 'append_context'.

        Args:
            item: The instance to add to the current context
        """
        if len(self.__parse_context) > 0:
            self.__parse_context[-1].add_line(item)
        else:
            self.__lines.append(item)

    def append_context(self, block):
        """ Extend the current context by adding the next level of hierarchy

        Args:
            block: PreprocessorBlock to append to the context stack
        """
        if not isinstance(block, PreprocessorBlock):
            raise PreprocessorError(report.error(
                "New context entry not of type PreprocessorBlock"
            ), path=self.path)
        self.push_to_current_context(block)
        self.__parse_context.append(block)

    def pop_context(self):
        """ Move a layer up the block hierarchy. """
        return self.__parse_context.pop()

    def add_parsed_document(self, document):
        """ Link a parsed document to this source file

        Link a parsed version of the document back to the source code - object
        type is arbitrary and not checked. Multiple documents can come from one
        source file.

        Args:
            document: The object parsed from this source file
        """
        if not document in self.__documents:
            self.__documents.append(document)

    def get_parsed_documents(self, en_includes=False, included=[]):
        """ Return all documents that have been parsed from this file.

        Return all of the parsed documents generated from this source file. Note
        that the object types within the array are arbitrary and may differ.
        Optionally the call can also return all documents in included files as well.

        Args:
            en_includes: Includes parsed documents from #include'd files, this
                         performs a recursive call to get_parsed_documents.
            included   : Tracks already included files to avoid infinite loop

        Returns:
            list: All of the documents attached to this file
        """
        all_docs = self.__documents[:]
        if en_includes:
            for file in [x for x in self.__includes if x not in included]:
                included.append(file)
                # Locate and import the associated PreprocessorFile
                inc_file = self.__preprocessor.find_file(self.__scope, file)
                # Check we got the file
                if inc_file:
                    # Check the file has been evaluated
                    if not inc_file.evaluated:
                        raise PreprocessorError(report.error(
                            f"Included files {file} has not yet been evaluated"
                        ), path=self.path)
                    # Include all documents
                    inc_docs = inc_file.get_parsed_documents(
                        en_includes=True, included=included
                    )
                    # NOTE: We manually check for duplication, rather than using
                    #       a set, as we want to maintain ordering!
                    for doc in inc_docs:
                        if doc not in all_docs:
                            all_docs.append(doc)
                elif not self.__force_resolve:
                    raise PreprocessorError(report.error(
                        f"Could not locate file {file} - has it been parsed out-of-order?"
                    ), path=self.path)
        return all_docs

    def resolve_value(self, value, line=None):
        """ Convert any string into its final value using defined constants

        Args:
            value: The value to resolve
            line : The PreprocessorLine instance this value came from

        Returns:
            value: The result of the evaluation
        """
        # Check for '<' and '>' bracing and remove if present
        if isinstance(value, str):
            for match in re.finditer(r"<([\w]+)>", value):
                value = value.replace(match.group(0), match.group(1), 1)
        # Check if this value is a primative type?
        if type(value) in [bool, int, float]:
            return value
        # Check if the value can be converted to a number easily?
        elif value.replace('.','').isdigit():
            return float(value) if '.' in value else int(value)
        # See if this value is defined in the environment
        elif value in os.environ:
            # Treat 'yes', 'no', 'true', and 'false' as boolean values
            if value in os.environ and isinstance(value, str):
                if os.environ[value].lower().strip() in ['yes', 'true']:
                    return True
                elif os.environ[value].lower().strip() in ['no', 'false']:
                    return False
            elif not value in os.environ:
                return False
            # Otherwise just try to evaluate the environment variable
            # NOTE: We don't call resolve_value, as this would result in the value
            #       being referenced against the internal scope - not good.
            try:
                return eval(os.environ[value])
            except NameError:
                PreprocessorError(report.error(
                    f"Couldn't resolve environment variable '{value}' to an "
                    f"integer or boolean value."
                ), path=(line.source_file.path if line.source_file else None))
        # See if value is defined in this file or included files (expensive)
        else:
            all_defines = self.list_all_defines()
            if value in all_defines:
                return self.resolve_value(all_defines[value], line)
            else:
                constants = re.findall(r"([A-Za-z]{1}[A-Za-z0-9_]+)", value)
                for val in constants:
                    if val in all_defines:
                        value = value.replace(val, str(self.resolve_value(all_defines[val], line)), 1)
                    else:
                        return None
                # NOTE: We replace '/' with '//' to perform integer division
                value = value.replace('/','//').replace('///','//')
                try:
                    return eval(value)
                except SyntaxError as e:
                    msg  = f"Couldn't evaluate '{e.text}' due to invalid syntax"
                    path = None
                    if line:
                        path  = line.source_file.path
                        msg  += f" on line {line.input_line} of file {path}"
                    raise PreprocessorError(report.error(msg), path=path) from e

    def load_file(self):
        """ Load file from disk and parse preprocessor syntax

        Load the contents of the file from disk, evaluating each line and generating
        the full hierarchy of PreprocessorBlocks with PreprocessorStatements.
        """
        if len(self.__lines) > 0:
            raise PreprocessorError(report.error(
                "File has already been loaded into PreprocessorFile"
            ), path=self.path)
        elif not os.path.exists(self.__path) or os.path.isdir(self.__path):
            raise PreprocessorError(report.error(
                f"Could not open file at path: {self.__path}"
            ), path=self.path)

        report.debug(f"Loading file {self.__path}")

        with open(self.__path, 'r') as fh:
            line_no = 0
            line    = fh.readline()
            while line:
                # Remove any line return characters
                line = PreprocessorLine(line.replace('\n','').replace('\r',''))
                line.input_line  = line_no
                line.source_file = self
                # Test each regular expression against the line to see if we
                # have a match
                matched = None
                for key in preprocessor_regex.keys():
                    rgx = preprocessor_regex[key]
                    if rgx.match(line) != None:
                        matched = key
                        break
                regex = preprocessor_regex[matched] if matched else None
                # Perform the correct action based on the matched regex
                if matched == None:
                    self.push_to_current_context(line)

                elif matched in ['include', 'define']:
                    statement = PreprocessorStatement(line, regex, self)
                    self.push_to_current_context(statement)

                elif matched == 'if':
                    statement = PreprocessorStatement(line, regex, self)
                    block     = PreprocessorIfBlock(self)
                    block.add_section(statement)
                    self.append_context(block)

                elif matched in ['elif', 'else']:
                    statement = PreprocessorStatement(line, regex, self)
                    block     = self.get_current_context()
                    if not isinstance(block, PreprocessorIfBlock):
                        raise PreprocessorError(report.error(
                            "Trying to append to incorrect block type"
                        ), path=self.path)
                    block.add_section(statement)

                elif matched == 'endif':
                    block = self.get_current_context()
                    if not isinstance(block, PreprocessorIfBlock):
                        raise PreprocessorError(report.error(
                            "Trying to close non-IF block with '#endif'"
                        ), path=self.path)
                    self.pop_context()

                elif matched == 'for':
                    statement = PreprocessorStatement(line, regex, self)
                    block     = PreprocessorForBlock(statement, self)
                    self.append_context(block)

                elif matched == 'endfor':
                    block = self.get_current_context()
                    if not isinstance(block, PreprocessorForBlock):
                        raise PreprocessorError(report.error(
                            "Trying to close non-FOR block with '#endfor'"
                        ), path=self.path)
                    self.pop_context()

                else:
                    raise PreprocessorError(report.error(
                        f"Matched unsupported regular expression {matched}"
                    ), path=self.path)

                # Read the next line
                line_no += 1
                line     = fh.readline()

    def evaluate(self):
        """ Evaluate the contents of this PreprocessorFile

        Run the evaluation to construct the 'final' line array, expanding all
        blocks based on the evaluated result of statements. Note that this call
        returns the PreprocessorFile object and not the line array, this is so
        later stages can relate parsed documents back to the source code.

        Returns:
            PreprocessorFile: This instance, allowing for chaining of commands.
        """
        # Check if this file has been loaded?
        if not self.loaded:
            self.load_file()

        report.debug(f"Evaluating file {self.__path}")

        # Define a function to recursively expand the lines in the file, this
        # deals with #include and #define tags within a block
        def expand_lines(lines):
            result = []
            for line in lines:
                # For a normal line, include it verbatim
                if isinstance(line, PreprocessorLine):
                    result.append(line)
                # For #include and #define statements, evaluate them
                elif isinstance(line, PreprocessorStatement):
                    if line.type == 'define':
                        pair = line.evaluate()
                        report.debug(f"File {self.__path} defines {pair['key']}=${pair['value']}")
                        self.set_definition(pair['key'], pair['value'])
                    elif line.type == 'include':
                        to_incl = line.evaluate().strip()
                        if len(to_incl) > 0:
                            report.debug(f"File {self.__path} includes file {to_incl}")
                            self.include_file(to_incl)
                            # Keep the include, so we can insert other files at the right point
                            result.append(line)
                        else:
                            report.warning(
                                f"Include statement is blank in {self.__path} on "
                                f"line {line.line.input_line}"
                            )
                    else:
                        raise PreprocessorError(
                            "Unsupported PreprocessorStatement type", path=self.path
                        )
                # For a block - recurse to evaluate embedded #include and #define
                elif isinstance(line, PreprocessorBlock):
                    result += expand_lines(line.evaluate())
                # For any other type, barf
                else:
                    raise PreprocessorError("Unsupported line type", path=self.path)
            return result

        # Expand blocks - but not yet replacing uses of #define'd variables
        primary = expand_lines(self.__lines)
        report.debug(f"Block evaluation completed for {self.__path}")

        # Ensure that the include files list is unique
        self.__includes = list(set(self.__includes))

        # Calculate all values defined in the scope, so that we can replace them
        all_defines = self.list_all_defines()
        def_keys    = all_defines.keys()
        all_values  = {}
        for key in def_keys:
            all_values[key] = self.resolve_value(all_defines[key])

        # Get the list of all files included one level down
        already_included = self.all_included_files(top=False, recursive=True)

        # Build the final version of the file, replacing any usages of #define'd
        # values - either explicit (contained in '<...>') or implicit.
        self.__final = []
        explicit_rgx = re.compile(r"[<]([A-Za-z]{1}[A-Za-z0-9_]+)[>]")
        implicit_rgx = re.compile(r"[^A-Za-z0-9<]{0,1}([A-Za-z]{1}[A-Za-z0-9_]+)[^A-Za-z0-9>]{0,1}")
        line_no = 1
        for line in primary:
            # Embed included files into the buffer at the right point
            if isinstance(line, PreprocessorStatement):
                if not line.type == 'include':
                    raise PreprocessorError(
                        report.error('Unsupported PreprocessorStatement type'),
                        path=self.path
                    )
                incl_path = line.evaluate().strip()
                incl      = self.__preprocessor.find_file(self.__scope, incl_path)
                # If the file has already been embedded, skip over it
                if incl in already_included:
                    continue
                # Embed the result of the file into the full result
                sub_result    = incl.get_result()
                self.__final += sub_result
                line_no      += len(sub_result)
            # For lines directly from this file, ensure they are fully evaluted
            elif isinstance(line, PreprocessorLine):
                original = line
                assert original.input_line >= 0
                # Explicit matches first
                matches = explicit_rgx.findall(line)
                for match in [x for x in matches if x.strip() in def_keys]:
                    # NOTE: Only replace the first occurrence to avoid partial replacement!
                    line = line.replace(f"<{match}>", str(all_values[match.strip()]), 1)
                # Implicit matches second (not contained in angle brackets)
                matches = implicit_rgx.findall(line)
                for match in [x for x in matches if x.strip() in def_keys]:
                    # NOTE: Only replace the first occurrence to avoid partial replacement!
                    line = line.replace(f"{match}", str(all_values[match.strip()]), 1)
                # Convert back to a PreprocessorLine if necessary
                if not isinstance(line, PreprocessorLine):
                    line = PreprocessorLine(line)
                    line.source_file = self
                    line.input_line  = original.input_line
                # Attach the line number in the output file
                line.output_line = line_no
                # Store the final version of the line
                self.__final.append(line)
                line_no += 1

        # If we've got here, then evaluation was successful
        self.__evaluated = True

        report.debug(f"Evaluation completed for {self.__path}")

        return self
