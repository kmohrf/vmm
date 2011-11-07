# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2011, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.pycompat

    VirtualMailManager's compatibility stuff for Python 2.4
"""

# http://docs.python.org/library/functions.html#all
try:
    all = all
except NameError:
    def all(iterable):
        """Return True if all elements of the *iterable* are true
        (or if the iterable is empty).

        """
        for element in iterable:
            if not element:
                return False
        return True


# http://docs.python.org/library/functions.html#any
try:
    any = any
except NameError:
    def any(iterable):
        """Return True if any element of the *iterable* is true.  If the
        iterable is empty, return False.

        """
        for element in iterable:
            if element:
                return True
        return False
