import sys
import os
from subprocess import call

def create_header():
    header = bytearray('\0' * (32))
    # Tag : 8 bytes
    header[0]='['
    header[1]='*'
    header[2]='I'
    header[3]='O'
    header[4]='P'
    header[5]='C'
    header[6]='*'
    header[7]=']'

    # Header Major Version : 1 byte
    header[8]='1'
    # Header Minor Version : 1 byte
    header[9]='0'

    return header

def overwrite_to(offset, src, dst):
    fp = open(dst, "r+b")
    fp.seek(offset)
    fp.write(src)
    fp.close()

def help():
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        help()

    storage_dev = sys.argv[1]

    header = create_header()
    overwrite_to(0x100000, header, storage_dev)
