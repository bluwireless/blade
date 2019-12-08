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

import ast
from math import ceil, log
import os
import re

# Get hold of the report
from .. import reporting
report = reporting.get_report("elaborator.common")

from designformat import DFBase, DFConstants
from ..preprocessor import PreprocessorFile
from ..schema import Def, Mod, His, Reg
from ..schema.ph_tag_base import CONSTANTS as PHConstants

class ElaborationError(Exception):
    """ Custom Exception type that allows elaboration errors to be reported """

    def __init__(self, message, ph_doc=None):
        """ Initialise the elaboration error.

        Args:
            message: The exception message
            ph_doc : The YAML document that failed to elaborate
        """
        super().__init__(message)
        self.ph_doc = ph_doc

class ElaboratorScope(object):
    """
    Defines the scope that the elaborator can use to find module declarations
    (!Mod), resolve defined constants (!Def), lookup interconnect definitions
    (!His), etc.
    """

    def __init__(self):
        """ Initialise the scope and any maps for holding lookups. """
        self.__docs = {}

    def add_document(self, document):
        """ Add a document to the scope, automatically classifying it's type

        Args:
            document: The document to add
        """
        # Ensure storage for this document type exists
        doc_id   = document.name.strip().lower()
        doc_type = type(document).__name__
        if not doc_type in self.__docs:
            self.__docs[doc_type] = {}
        # Check this document is named (otherwise can't be retrieved)
        if document.name == None or len(document.name.strip()) == 0:
            raise ElaborationError(
                report.error(
                    f"Cannot add document of type {type(document)} without name to scope",
                    item=document
                ),
                ph_doc=document
            )
        # Check this document won't clash with another already stored
        elif doc_id in self.__docs[doc_type]:
            # Allow multiple definitions of a constant, as long as the value matches!
            if isinstance(document, Def) and document.val == self.__docs[doc_type][doc_id].val:
                return
            else:
                report.warning(
                    f"{document.name} (type {doc_type}) already exists in scope: \n"
                    f" -> {document.source.path}\n"
                    f" -> {self.__docs[doc_type][doc_id].source.path}"
                )
        # Store the document
        else:
            self.__docs[doc_type][doc_id] = document

    def get_document(self, name, expected=None):
        """ Retrieve a document by name from the scope of any type

        Args:
            name     The name of the document to retrieve
            expected If a type is specified, compatibility will be checked (optional)
        """
        doc_type   = expected.__name__ if expected else None
        clean_name = name.strip().lower()
        # If we know the type, then we can resolve directly
        if doc_type:
            if doc_type not in self.__docs or clean_name not in self.__docs[doc_type]:
                return None
            else:
                return self.__docs[doc_type][clean_name]
        # If we don't know the type, then search for document only by name
        else:
            for doc_map in self.__docs.values():
                if clean_name in doc_map:
                    return doc_map[clean_name]
            return None

    @property
    def defs(self):
        return self.__docs[Def.__name__].values() if Def.__name__ in self.__docs else None

    @property
    def mods(self):
        return self.__docs[Mod.__name__].values() if Mod.__name__ in self.__docs else None

    @property
    def his(self):
        return self.__docs[His.__name__].values() if His.__name__ in self.__docs else None

    @property
    def regs(self):
        return self.__docs[Reg.__name__].values() if Reg.__name__ in self.__docs else None

    def evaluate_expression(self, expression, ref_cb=None, ref_ctx=None):
        """
        Evaluate an expression from Phhidle's YAML description, performing any
        required subsitution of named constants referencing !Def values.

        Args:
            expression: What to evaluate
            ref_cb    : Callback to evaluate references (optional)
            ref_ctx   : A context object to provide to the reference callback (optional)
        """
        # Keep track of the original expression
        original = expression

        # Check if the expression appears to be a number or boolean value
        if type(expression) in [int, bool, float]:
            return expression
        elif expression.replace(".","").isdigit():
            return float(expression) if "." in expression else int(expression)
        elif isinstance(expression, str) and len(expression.strip()) == 0:
            return None

        # Clean up any leading or trailing whitespace
        expression = str(expression).strip()

        # Find and replace any cross-references
        # NOTE: We are expecting a multi-part reference separated by '/', e.g.
        #       'A/B/C(/D)/E'. There must be at least three sections (2 x '/')
        #       before it will be recognised, and sections may be left blank in
        #       which case the scope is not changed.
        crossrefs = re.findall(
            r"(?:^|[^\w\/])([\w]+(?:\/[\w]{0,}){2,})(?:$|[^\w\/])", expression
        )
        for crossref in crossrefs:
            if ref_cb == None:
                raise ElaborationError(
                    f"Detected cross-reference, but no callback provided: {expression}"
                )
            # Split the crossrefence on a delimeter of '/'
            parts = [x.strip() for x in crossref.split('/')]
            # Remote any empty 'parts' from the array
            parts = [x for x in parts if len(x.strip()) > 0]
            # Ask the callback to resolve the value
            # NOTE: We support nested cross-references by calling eval again
            value, new_ctx = ref_cb(xref=parts, scope=self, ctx=ref_ctx)
            # NOTE: The context can be changed by the callback to allow 'self'
            #       to be resolved correctly in nested references.
            value = self.evaluate_expression(value, ref_cb=ref_cb, ref_ctx=new_ctx)
            # Only replace one occurrence to avoid partial string replacement
            expression = expression.replace(crossref, str(value), 1)

        # Find and replace any self-references, denoted a '$' prefix
        selfrefs = re.findall(r"(?:^|[^\w$])+[$]([\w]+)\b", expression)
        for selfref in selfrefs:
            if ref_cb == None:
                raise ElaborationError(
                    f"Detected self-reference, but no callback provided: {expression}"
                )
            # Resolve the reference value
            # NOTE: We support nested cross-references by calling eval again
            value, new_ctx = ref_cb(ref=selfref, scope=self, ctx=ref_ctx)
            # NOTE: The context can be changed by the callback to allow 'self'
            #       to be resolved correctly in nested references.
            value = self.evaluate_expression(value, ref_cb=ref_cb, ref_ctx=new_ctx)
            # Only replace one occurrence to avoid partial string replacement
            expression = expression.replace(f"${selfref}", str(value), 1)

        # Find and replace any constant values we can
        constants = re.findall(r"([A-Za-z]{1}[A-Za-z0-9_]+)", expression)
        for constant in constants:
            const_def = self.get_document(constant, expected=Def)
            if const_def != None:
                # One constant may reference another, so recurse
                value = self.evaluate_expression(const_def.val)
                # Only replace one occurrence to avoid partial string replacement
                expression = expression.replace(constant, str(value), 1)

        # Evaluate the expression
        try:
            return eval(expression)
        except SyntaxError as e:
            raise ElaborationError(
                f"Expression could not be evaluated '{expression}' ('{original}')"
            ) from e
        except NameError as e:
            raise ElaborationError(
                f"Expression could not be fully resolved '{original}'"
            ) from e

def options_to_attributes(ph_src, df_tgt):
    """ Converts Phhidle YAML 'options' into DFBase 'attributes'.

    Args:
        ph_src: The Phhidle source object (to take options from)
        df_tgt: The DesignFormat target object (to set attributes on)
    """
    if not isinstance(df_tgt, DFBase):
        raise Exception(f"Target is not a valid DesignFormat object: {type(df_tgt).__name__}")
    if ph_src.options:
        src = ph_src.options if isinstance(ph_src.options, list) else [ph_src.options]
        for opt in src:
            if '=' in opt:
                parts = opt.split('=')
                df_tgt.setAttribute(parts[0], parts[1])
            else:
                df_tgt.setAttribute(opt, True)

def tag_source_info(ph_src, df_tgt):
    """
    Appends a number of attributes to a DesignFormat object detailing the source
    YAML file. This is used by template generation to locate header files, scripts,
    and other resources by absolute paths.

    Args:
        ph_src: The Phhidle source object
        df_tgt: The DesignFormat target object
    """
    if not isinstance(df_tgt, DFBase):
        raise Exception(f"Target is not a valid DesignFormat object: {type(df_tgt).__name__}")
    # Check we have a source object
    if not isinstance(ph_src.source, PreprocessorFile):
        return
    # Get the source path
    src_path = ph_src.source.path
    df_tgt.setAttribute('source_path', src_path)
    # Try to work out the repository from the path
    # NOTE: This relies on the path being ${WORK_AREA}/<repo>/<version>/view/...
    #       or (for verification) ${IMPORT_WORK_AREA}/<repo>/<version>/view/...
    replacements = ['WORK_AREA', 'IMPORT_WORK_AREA']
    if any((x for x in replacements if x in os.environ)):
        rel_path = src_path
        # Make any replacements possible
        for key in replacements:
            if key in os.environ and os.environ[key].strip() in rel_path:
                rel_path = rel_path.replace(os.environ[key].strip(), '').lstrip(os.path.sep)
        # Take the repository name as the first path segment
        df_tgt.setAttribute('source_repo', rel_path.split(os.path.sep)[0])

role_mapping = {
    PHConstants.ROLES.MASTER : DFConstants.ROLE.MASTER,
    PHConstants.ROLES.SLAVE  : DFConstants.ROLE.SLAVE,
    PHConstants.ROLES.BI     : DFConstants.ROLE.BIDIR,
    PHConstants.ROLES.UNKNOWN: DFConstants.ROLE.BIDIR,
}
def map_ph_to_df_role(role):
    """ Convert a Phhidle role to its equivalent in DesignFormat.

    Args:
        role: The Phhidle role to convert
    """
    global role_mapping
    if not role in role_mapping:
        raise KeyError(f"Unknown Phhidle YAML role '{role}'")
    return role_mapping[role]