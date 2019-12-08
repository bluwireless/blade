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

import logging

# Setup logging
logger = logging.getLogger(__name__)

from .common import ElaborationError

from ..schema import Def
from designformat import DFDefine

def elaborate_define(top, scope, max_depth=None):
    """ Evaluate a !Def instance, returning a DFDefine with resolve value.

    Args:
        top      : The top-level !Def to evaluate
        scope    : An ElaboratorScope object containing all documents included
                 : directly or indirectly by the top module.
        max_depth: Ignored for now

    Returns:
        DFDefine: DesignFormat object containing the defined value
    """
    # Build the new define
    define = DFDefine(
        top.name,
        scope.evaluate_expression(top.val),
        top.ld if top.ld and len(top.ld.strip()) > 0 else top.sd
    )

    # Return the define
    return define
