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

from distutils.core import setup

setup(
    name="BLADE",
    version="1.0",
    license=['GNU General Public License v3.0'],
    description=
        "Hardware Architecture and Implementation Autogeneration for SoC Designers"
    ,
    author='Blu Wireless Ltd',
    packages=[
        'blade', 'blade.checkers', 'blade.elaborate', 'blade.preprocessor',
        'blade.reporting', 'blade.schema',
    ],
    data_files=[
        'LICENSE',
        'blade/reporting/templates/blocks.html.mk',
        'blade/reporting/templates/report.html.mk',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': ['blade=blade.__main__:main']
    },
    install_requires=[
        'designformat',
        'pyyaml',
        'mako',
        'tqdm',
        'designformat',
    ],
    extras_require={
        "documentation": [
            'sphinx',
            'recommonmark',
            'sphinx-markdown-tables',
            'sphinx-rtd-theme',
        ],
    },
)