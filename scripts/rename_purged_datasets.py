#!/usr/bin/env python2.4
"""
Renames a dataset file by appending _purged to the file name so that it can later be removed from disk.
Usage: python2.4 rename_purged_datasets.py purge.log
"""

import sys, os

def main():
    infile = sys.argv[1]
    outfile = infile + ".renamed.log"
    out = open( outfile, 'w' )
    
    print >> out, "# The following renamed datasets can be removed from disk"
    i = 0
    for i, line in enumerate( open( infile ) ):
        line = line.rstrip( '\r\n' )
        if line and line.startswith( '/var/opt/galaxy/main/database/files/dataset_' ):
            try:
                purged_filename = line + "_purged"
                os.rename( line, purged_filename )
                print >> out, purged_filename
            except Exception, exc:
                print >> out, "# Error, exception " + str( exc ) + " caught attempting to rename " + purged_filename
    print >> out, "# Renamed " + str( i ) + " files"    

if __name__ == "__main__":
    main()