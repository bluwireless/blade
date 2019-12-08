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

class RuleViolation():
    """ A non-critical rule violation which are collected as a check runs """

    def __init__(self, message, node):
        """ Initialise the rule violation

        Args:
            message: The violation error message
            node   : The DesignFormat node that failed
        """
        self.message = message
        self.node    = node

class CriticalRuleViolation(Exception, RuleViolation):
    """
    Custom exception type for reporting critical rule violations - this should
    be used when a violation is so critical that it aborts the rest of the check
    """

    def __init__(self, message, node):
        Exception.__init__(self, message)
        RuleViolation.__init__(self, message, node)

