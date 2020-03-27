#!/bin/python2.7

import struct
import pprint
import sys
import ConfigParser
import binascii
import json
from subprocess import call

def execmd(cmd):
    print cmd
    return call(cmd)

def help():
    print "usage: dao_sfs.py <platform dao dir> <output squashfs>"
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        help()
    platforms_dir = sys.argv[1]
    squashfs_file = sys.argv[2]
    CMD=['sudo', 'mksquashfs', platforms_dir, squashfs_file, '-noappend', '-all-root', '-comp', 'xz']
    execmd(CMD)
