# coding=utf-8
import codecs
from args import args
from parse_alignments import parse_nbest


def make_fast_align_txt(source_list, filename):
    """                                                                        
    Makes a text file in the input format fast align accepts.                  
    """
    with codecs.open(filename, "w", encoding='utf-8') as f:
        f.writelines(repr(source) for source in source_list)

source_list = parse_nbest(args.nbest, args.tagged_source, args.lang)
make_fast_align_txt(source_list, '{}/fast_align_input'.format(args.outdir))
