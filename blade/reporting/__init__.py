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

from datetime import datetime
import os

from .render import Renderer

class ReportCommon(object):
    """ Provide constants required by reporting within a single namespace """

    # Declare a colour chart (bash colour codes)
    COLOURS = {
        "red"   : 31,
        "green" : 32,
        "yellow": 33,
        "blue"  : 34,
        "purple": 35,
        "cyan"  : 36
    }

    # Define priority levels
    DEBUG   = 40 # Most verbose, used for debugging internals of BLADE
    INFO    = 30 #
    WARNING = 20 # Warning messages
    ERROR   = 10 # Error messages, usually prior to aborting elaboration
    NONE    =  0 # No associated verbosity, always print

    # Declare a mapping between priority and name
    PRIORITY_MAP = {
        DEBUG  : "DEBUG",
        INFO   : "INFO",
        WARNING: "WARNING",
        ERROR  : "ERROR",
        NONE   : "NONE"
    }

    # Declare a mapping between priority and colour
    COLOUR_MAP = {
        WARNING: COLOURS["yellow"],
        ERROR  : COLOURS["red"],
        INFO   : COLOURS["cyan"]
    }

class ReportableObject(object):
    """ Provide a base object reportable item. """

    def __init__(self, title, root=None, parent=None):
        """
        Initialise the base reportable object with a title, it will also capture
        the date that the reportable item was recorded

        Args:
            title : Title of the item being reported
            root  : Reference to the root node (if this isn't it)
            parent: Reference to the parent node (if present)
        """
        self.__date    = datetime.now()
        self.__title   = title
        self.__root    = (root if root != None else self)
        self.__parent  = parent

    # Read-only property accessors
    @property
    def date(self): return self.__date

    @property
    def title(self): return self.__title

    @property
    def root(self): return self.__root

    @property
    def parent(self): return self.__parent

    @property
    def path(self):
        """ Full hierarchical path """
        return (self.parent.path + "." if self.parent else "") + self.title

    def summarise(self):
        """ Produce a single object summarising the report item. """
        return { 'date': self.__date.isoformat(), 'title': self.__title }

class ReportItem(ReportableObject):
    """
    Stores a logged item of data that should be included in any report generated
    at the end of the BLADE elaboration.
    """

    def __init__(self, title, body, priority=ReportCommon.NONE, root=None, parent=None, **kwargs):
        """
        Initialise the report item, capturing the logged date and any passed
        parameters.

        Args:
            title   : Title of the message being logged
            body    : Message being logged
            priority: What level of severity is this message (debug, error, etc)
            root    : Reference to the root node
            parent  : Reference to the parent node
            kwargs  : Any arbitary data
        """
        super().__init__(title, root, parent)
        self.__priority = priority
        self.__body     = body
        self.__extra    = kwargs if kwargs else {}

    # Read-only property accessors
    @property
    def priority(self): return self.__priority

    @property
    def body(self): return self.__body

    @property
    def extra(self): return self.__extra

    # Full hierarchical path (excludes my title)
    @property
    def path(self):
        return (self.parent.path if self.parent else "")

    def summarise(self):
        """ Produce a single object summarising the report item. """
        return {
            **super().summarise(),
            **{
                'path'    : self.path,
                'priority': ReportCommon.PRIORITY_MAP[self.__priority],
                'body'    : self.__body,
                'extra'   : self.__extra
            }
        }

class ReportCategory(ReportableObject):
    """
    Stores related report items within a single category. Categories can be
    nested to achieve greater granularity
    """

    def __init__(self, title, root=None, parent=None):
        """ Initialise the category with a specified name

        Args:
            title : Title of the category
            root  : Reference to the root node
            parent: Reference to the parent node
        """
        super().__init__(title, root, parent)
        self.__contents = []

    # Read-only property accessors
    @property
    def contents(self): return self.__contents

    def lookup_item(self, path):
        """ Find an item with a specified name

        Args:
            path: Path within the report namespace
        """
        parts        = path.split('.')
        next_segment = parts[0]
        remainder    = ".".join(parts[1:]).strip()
        viable       = [x for x in self.__contents if x.title == next_segment]
        if len(viable) == 0:
            return None
        elif len(viable) > 1:
            raise Exception(f"More than one option is available for key: {next_segment}")
        elif type(viable[0]) != ReportCategory and len(remainder) > 0:
            raise Exception(f"Cannot resolve path to non-category object: {remainder}")
        elif type(viable[0]) == ReportCategory and len(remainder) > 0:
            return viable[0].lookup_item(remainder)
        else:
            return viable[0]

    def create_category(self, path):
        """
        Create a category including all intermediate categories if they don't
        already exist.

        Args:
            path: Hierarchical path to create (segments separated by '.')
        """
        parts = [x.strip() for x in path.split(".")]
        last  = self
        for part in parts:
            child = last.lookup_item(part)
            if not child:
                child = ReportCategory(
                    part,
                    root=(self.root if self.root else self),
                    parent=last
                )
                last.add_item(child)
            last = child
        return last

    def get_category(self, path):
        """ Get a category by path, create it if it doesn't exist

        Args:
            path: Hierarchical path to retrieve (segments separated by '.')
        """
        # Find the category
        category = self.lookup_item(path)
        # Create the hierarchy down to the desired category (if it doesn't exist)
        if not category: category = self.create_category(path)
        # Return the category
        return category

    def __log(self, priority, path_or_title, title=None, body=None, **kwargs):
        """ Log a new item into the report with title, body, date, and attributes.

        Args:
            priority     : Level this entry is logged at.
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        # If no title is provided, assume it's the third argument
        path  = (None          if title == None else path_or_title)
        title = (path_or_title if title == None else title        )
        # Get the category
        category = self.get_category(path) if path != None else self
        # Create and store the report item
        category.add_item(ReportItem(
            title, body, priority=priority, parent=self, root=self.root, **kwargs
        ))
        # If the priority is <= the verbosity, log the message
        if priority <= self.root.verbosity:
            self.root.print_message(priority, path if path else self.path, title)
        # Return the title so we can chain
        return title

    def error(self, path_or_title, title=None, body=None, **kwargs):
        """ Record a new error into the report

        Args:
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        return self.__log(ReportCommon.ERROR, path_or_title, title, body, **kwargs)

    def warning(self, path_or_title, title=None, body=None, **kwargs):
        """ Record a new warning into the report

        Args:
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        return self.__log(ReportCommon.WARNING, path_or_title, title, body, **kwargs)

    def info(self, path_or_title, title=None, body=None, **kwargs):
        """ Record a new info message into the report

        Args:
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        return self.__log(ReportCommon.INFO, path_or_title, title, body, **kwargs)

    def debug(self, path_or_title, title=None, body=None, **kwargs):
        """ Record a new debug message into the report

        Args:
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        return self.__log(ReportCommon.DEBUG, path_or_title, title, body, **kwargs)

    def critical(self, path_or_title, title=None, body=None, **kwargs):
        """ Record a critical error into the report (always printed)

        Args:
            path_or_title: Either a hierarchical path to the category to report
                           in, or the title of the entry to log
            title        : If given a path, this is the title
            body         : Body of the log entry
            kwargs       : Extra parameters to associate
        """
        return self.__log(ReportCommon.NONE, path_or_title, title, body, **kwargs)

    def add_item(self, item):
        """ Add a new item to the category.

        Args:
            item: Item to add - must inherit from ReportableObject.
        """
        if not issubclass(type(item), ReportableObject):
            raise Exception("Provided item does not inherit from ReportableObject")
        elif type(item) == ReportCategory and self.lookup_item(item.title) != None:
            raise Exception(f"Can't add a ReportCategory with a name matching an existing entry: {self.title}.{item.title}")
        self.__contents.append(item)

    def summarise(self, verbosity=ReportCommon.INFO):
        """ Produce a summary of this object

        Args:
            verbosity: Control the minimum verbosity to print out
        """
        return {
            **super().summarise(),
            "categories": [x.summarise(verbosity=verbosity) for x in self.__contents if isinstance(x, ReportCategory)],
            "contents"  : [x.summarise() for x in self.__contents if isinstance(x, ReportItem) and x.priority <= verbosity]
        }

class Report(ReportCategory):
    """ A top level object representing a report, inherits from ReportCategory. """

    def __init__(self, verbosity=ReportCommon.WARNING):
        """ Initialise the report

        Args:
            verbosity: The default verbosity to report at
        """
        super().__init__("BLADE Report")
        self.verbosity  = verbosity
        script_dir      = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
        self.__renderer = Renderer(os.path.join(script_dir, 'templates'))
        self.__colour   = ('TERM' in os.environ and os.environ['TERM'] and len(os.environ['TERM']) > 0)

    @property
    def verbosity(self):
        return self.__verbosity

    @verbosity.setter
    def verbosity(self, value):
        if value not in [
            ReportCommon.NONE, ReportCommon.ERROR, ReportCommon.WARNING, ReportCommon.INFO, ReportCommon.DEBUG
        ]:
            raise Exception(f"Invalid verbosity level {value}")
        self.__verbosity = value

    def print_message(self, priority, path, message):
        """ Print out a log message with the correct formatting

        Args:
            priority: The level (debug/info/warning/error) to print at
            path    : Hierarchical path of object being printed
            message : Message to print
        """
        global COLOURS
        log_msg = f"[{path}] " if path == self.title else f"[{path.replace(self.title + '.','')}] "
        if priority in ReportCommon.PRIORITY_MAP:
            log_msg += f"{ReportCommon.PRIORITY_MAP[priority]}: "
        log_msg += message
        if self.__colour and priority in ReportCommon.COLOUR_MAP:
            print(f"\033[1;{ReportCommon.COLOUR_MAP[priority]}m{log_msg}\033[0m")
        else:
            print(log_msg)

    def write_report(self, path, verbosity=ReportCommon.INFO):
        """ Generate an HTML report and write it to file

        Args:
            path     : Where to write the HTML report
            verbosity: Maximum verbosity to include in the report
        """
        self.__renderer.generate('report.html.mk', path, {
            'report': self.summarise(verbosity=verbosity)
        })

# A shared report instance
shared_report = Report()

def get_report(path=None):
    """ A function for getting a report category from the shared report instance """
    global shared_report
    if not path or len(path.strip()) == 0:
        return shared_report
    else:
        return shared_report.get_category(path)
