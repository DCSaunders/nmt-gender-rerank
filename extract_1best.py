from __future__ import print_function
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--out")
args = parser.parse_args()


with open(args.out, 'w') as fwrite:
    winomt_index = -1
    for line in sys.stdin:
        row = line.strip().split('|||')
        this_index = int(row[0])
        if this_index > winomt_index:
            fwrite.write(row[1].strip('\t'))
            fwrite.write('\n')
            winomt_index = this_index
