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

class ClassFromMap(object):
    """ Magic dictionary to nested namespace converter """
    __raw_dict = None
    __last_index = 0

    def __init__ (self, val_dict):
        self.__raw_dict = val_dict

    def keys(self):
        return self.__raw_dict.keys()

    def values(self):
        return self.__raw_dict.values()

    def __repr__(self):
        return self.__raw_dict.__repr__()

    def __getitem__(self, key):
        """ Override the [...] subscript accessor """
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__raw_dict:
            return self.__raw_dict[key]
        else:
            return None

    def __getattribute__(self, key):
        """ Override the '.' attribute accessor """
        try:
            result = super(ClassFromMap, self).__getattribute__(key)
            return result
        except AttributeError as e:
            if key in self.__raw_dict:
                return self.__raw_dict[key]
            else:
                raise e

    def __setattr__(self, key, value):
        """ Protect non-base class attributes from being overwritten """
        if self.__raw_dict and key in self.__raw_dict.keys():
            raise AttributeError("%s is a protected property" % key)
        else:
            super(ClassFromMap, self).__setattr__(key, value)

    def __iter__(self):
        """ Allow the object keys to be iterated """
        self.__last_index = 0
        return self

    def __next__(self):
        item = None
        if self.__last_index < len(self.keys()):
            item = list(self.keys())[self.__last_index]
            self.__last_index += 1
        else:
            raise StopIteration()
        return item
    next = __next__

def convert_to_class(map_in):
    """ Take a map object and convert it to a namespace using ClassFromMap """
    if not(isinstance(map_in, dict)):
        return map_in
    digested = {}
    for key in map_in:
        if type(map_in[key]) is dict:
            digested[key] = convert_to_class(map_in[key])
        elif type(map_in[key]) is list:
            digested[key] = [convert_to_class(x) for x in map_in[key]]
        else:
            digested[key] = map_in[key]
    return ClassFromMap(digested)
