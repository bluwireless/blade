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

from random import random, choice, randint
import string

## gen_string
#  Generate a random string with a length between two numbers, optionally
#  allowing spaces.
#
def gen_string(min_len=5, max_len=10, spaces=False):
    assert max_len >= min_len and min_len >= 1
    length = randint(min_len, max_len)
    if spaces:
        full_str = gen_string(min_len, max_len, spaces=False)
        while len(full_str) < length:
            full_str += " " + gen_string(min_len, max_len, spaces=False)
        return full_str
    else:
        chars  = string.ascii_letters
        return "".join(str(choice(chars)) for i in range(length))

## gen_fake_path
#  Generate a fake path string, random strings separated by forward slashes
#
def gen_fake_path(min_sections=3, max_sections=6):
    num_sections = randint(min_sections, max_sections)
    sections = [gen_string(spaces=False) for i in range(num_sections)]
    return "/" + "/".join(sections)

## rand_value
#  Generate a random value string, integer, or boolean
#
def rand_value():
    val_type = random() % 3
    if   val_type == 0: return gen_string(spaces=True)
    elif val_type == 1: return random()
    elif val_type == 2: return rand_boolean()

## rand_boolean
#  Generate a random boolean value
#
def rand_boolean():
    return True if (random() % 2) == 0 else False