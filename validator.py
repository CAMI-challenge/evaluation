#!/usr/bin/env python
"""
A simple tool for validating CAMI file formats.
"""
import cami.io
import argparse
import sys

parser = argparse.ArgumentParser(description='A simple tool for validating CAMI file formats.')
parser.add_argument('input_file', help='The file to validate')
parser.add_argument('-t', '--type', help='File type [binning, profile]', required=True, nargs=1)
args = parser.parse_args()

try:
    reader_class = None
    if args.type[0] == 'binning':
        print 'Validating input file as a CAMI binning file'
        reader_class = cami.io.BinningReader
    elif args.type[0] == 'profile':
        print 'Validating input file as a CAMI profile file'
        reader_class = cami.io.ProfileReader
    else:
        raise RuntimeError('Unknown file type {0}'.format(args.type))

    with reader_class(args.input_file) as reader:
        print 'Header information:'
        reader.print_headerinfo(sys.stderr)
        print
        print 'Data fields:'
        print >> sys.stderr, reader.column_definition
        mr = []
        for nrow, row in enumerate(reader, start=1):
            print >> sys.stderr, row
            mr.append(row)
        print
        print 'Read {0} data rows, check that this is correct.'.format(nrow)
        print 'VALIDATION OK.'

except IOError as e:
    print 'VALIDATION FAILED.'
    print 'Exception: {0}'.format(e)
    sys.exit(1)
