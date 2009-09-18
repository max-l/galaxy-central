#!/usr/bin/env python

from __future__ import division

import sys

import pkg_resources; pkg_resources.require( "bx-python" )
from bx.arrays.array_tree import *
from bx.arrays.wiggle import IntervalReader

def main():
   
    input_fname = sys.argv[1]
    out_fname = sys.argv[2]
    
    reader = IntervalReader( open( input_fname ) )
    
    # Fill array from wiggle
    d = array_tree_dict_from_wiggle_reader( reader, {} )
    
    for value in d.itervalues():
        value.root.build_summary()
    
    f = open( out_fname, "w" )
    FileArrayTreeDict.dict_to_file( d, f )
    f.close()

if __name__ == "__main__": 
    main()