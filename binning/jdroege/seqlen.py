#!/usr/bin/env python
"""
Jiffy to calculate sequence lengths in either FastA or FastQ format.
"""
from Bio import SeqIO
import os.path
import argparse
import sys

#
# CLI definition and parsing
#
parser = argparse.ArgumentParser(description='Calculate sequence lengths')
parser.add_argument('--fastq', help='Input file is fastq format', action='store_true', default=False)
parser.add_argument('input', help='Input file name', metavar='FILE')
args = parser.parse_args()

#
# Check if the supplied path exists and -- at least -- isn't a directory.
# This could still mean its a symlink to a directory..
#
if not os.path.exists(args.input) or os.path.isdir(args.input):
    print 'Error: {0} does not exist or is a directory'.format(args.input)
    sys.exit(1)

#
# Determine the specified file format
#
seqfmt = 'fasta'
if args.fastq:
    seqfmt = 'fastq'

#
# Read through the file input, one sequence at a time.
#
with open(args.input, 'r') as input_h:
    for r in SeqIO.parse(input_h, seqfmt):
        print '{0}\t{1}'.format(r.id, len(r))
