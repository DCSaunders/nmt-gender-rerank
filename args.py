import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--lang", default=None, help="Two-letter abbreviation for target language, e.g. de, es, he")
parser.add_argument("--outdir", default="/tmp/", help="Directory to write temporary and alignment files")
parser.add_argument("--outfile", default="/tmp/out_1best", help="File to write reranked output hypotheses")
parser.add_argument("--nbest", default=None, help="Path to file containing nbest list")
parser.add_argument("--tagged_source", help="Path to file containing token indices for gendered entities in source sentences, as determined using e.g. RoBERTa automatic pronoun disambiguation.Format index\tgender\tsentence")

args = parser.parse_args()
