#!/usr/bin/python
import struct, sys
for i in xrange(2**32):
    sys.stdout.write( struct.pack('I', i) )
