#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2007 - 2014, Pascal Volk
# See COPYING for distribution information.

"""This is the vmm main script."""

import sys

if __name__ == '__main__':
    # replace the script's cwd (/usr/local/sbin) with our module dir
    # (the location of the vmm directory) - if it is not in sys.path
    #sys.path[0] = '/usr/local/lib/vmm'
    # Otherwise just remove /usr/local/sbin from sys.path
    sys.path.remove(sys.path[0])
    from vmm.cli.main import run
    sys.exit(run(sys.argv))
