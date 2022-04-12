#!/bin/bash
#run in environment with environment variable $FAST_ALIGN_BASE pointing to root directory of fast_align (containing build directory)

LANG=$1
WDIR=$2
NBEST=$3
TAGS=$4
OUTF=$5
mkdir -p $WDIR

python make_align_input.py --tagged_source=$TAGS --lang=$LANG --outdir=$WDIR --nbest $NBEST

$FAST_ALIGN_BASE/build/fast_align -i $WDIR/fast_align_input -d -o -v -r > $WDIR/fast_align_output

python parse_alignments.py --tagged_source=$TAGS --lang=$LANG --outdir=$WDIR --nbest $NBEST --outfile=$OUTF
#python parse_alignments_inc_neutral.py --tagged_source=$TAGS --lang=$LANG --outdir=$WDIR --nbest $NBEST --outfile=$OUTF
