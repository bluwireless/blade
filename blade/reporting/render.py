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

from mako.lookup import TemplateLookup
from mako import exceptions

class Renderer(object):
    """
    Defines a basic renderer that uses Mako to produce output files from a template
    and an input context object.
    """

    def __init__(self, template_dir):
        self.__lookup = TemplateLookup(
            directories=[template_dir],
            imports    =[]
        )

    def generate(self, template, out_path, context):
        """
        Generate an output file using a specified template and a context object.

        Args:
            template: The template to render (must be within the lookup)
            out_path: The path to write the output file to
            context : The context object to pass to the renderer
        """
        if not os.path.isdir(os.path.dirname(os.path.abspath(out_path))):
            raise Exception(f"Could not write to path: {out_path}")
        with open(out_path, 'w') as fh:
            fh.write(self.__lookup.get_template(template).render(**context))
