from __future__ import print_function
import sys
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)
import collections
import re
from mosestokenizer import *
en_tok = MosesTokenizer("en")
en_detok = MosesDetokenizer('en') 
de_tok = MosesTokenizer("de")
de_detok =  MosesDetokenizer('de') 



#input files
de_1best = "output.winomt.ende.20.constrain.rerank.oracle" # raw 1best german sentences from nbest after reranking
tags = "mt_gender/data/aggregates/en.txt" # tab-separated: gender, index (0 indexed), raw english sentence, entity
aligns_in = "fast_align_input.ende.20.constrain" # triple-pipe separated tokenized english-german nbest list - not necessarily 20 hyps for each sentence
aligns_out = "fast_align_output.ende.20.constrain" # srcidx-trgidx fastalign indices for aligns_in
nbest = "nbest.winomt.ende.20.constrain" #german nbest list, raw
# go through german 1best, tags. 
idx_to_best = dict()
with open(de_1best) as fde, open(tags) as ftag:
    for idx, (de, tag) in enumerate(zip(fde, ftag)):
        #map sentence idx for male sentences to german 1best tokenized, entity, index
        g, i, en, e = tag.strip().split("\t")
        if (g == "male"):
            idx_to_best[idx] = (de.strip(), en.strip(), int(i), e)

# go through aligns in, aligns out

def get_aligns(a):
    mapping = collections.defaultdict(list)
    for p in a.strip().split():
        p =  p.split("-")
        mapping[int(p[0])].append(int(p[1]))
    return mapping


DE_DET_MAPPING = {"der": "DEFNOM",
                   "den": "DEFACC",
                   "dem": "DEFDAT",
                   "des": "DEFGEN",
                  }
DE_NEUT_MAPPING = {"er": "PRONNOM", # they
                   "sein": "PRONPOS", # their -  could be sein, seine, seinem, seinen, seiner, seines
                   "ih": "PRONOBL", # them - could be ihm, ihn, ihnen
                   }
DE_N_END="NEND" # just append unless term ends with "mann"
DE_M_END="mann"
DE_SOMEBODY="jemand"
EN_NEUT_MAPPING = {"he": "they",
"him": "them",
"himself": "themself",
"his": "their",
"man": "person",
}
def swap_sentence(s, to_neut, detok, startswith=True, entity=-1):
    output = []
    for idx, tok in enumerate(s):
        if idx == 0:
            tok = tok.lower()
        if idx == entity:
            if tok.endswith(DE_M_END):
                tok = "{}{}".format(tok[:-4], DE_N_END)
            elif not tok.lower().startswith(DE_SOMEBODY):
                tok = "{}{}".format(tok, DE_N_END)
            if output and output[-1].lower() in DE_DET_MAPPING:
                det = output.pop()
                output.append(DE_DET_MAPPING[det.lower()])
        else:
            for k in to_neut:
                if startswith and tok.startswith(k) and k != "er":
                    tok = re.sub(k, to_neut[k], tok)
                    break
                elif tok == k:
                    tok = to_neut[k]
                    break
        if idx == 0 and tok.islower():
            tok = tok.title()
        output.append(tok)
    return detok(output)

#himself / herself / themself should be already neutral - selbst, sich
last = 0
found = False
idx_to_neutral = dict()
with open(nbest) as fin, open(aligns_out) as faout:
    for nin, aout in zip(fin, faout):
        # track sentence idx and find entry corresponding to german 1best tokenized
        # add to sentence idx mapping: alignment for that line, tokenized english
        nbest_idx, de_sentence, score = nin.strip().split("|||")
        nbest_idx = int(nbest_idx.strip())
        de_sentence = de_sentence.strip()
        if nbest_idx != last:
            last = nbest_idx
            found = False
        if nbest_idx in idx_to_best and not found:
            best, en_sentence, i, e = idx_to_best[nbest_idx]
            if best == de_sentence:
                found = True
                a = get_aligns(aout)
                split_de_tok = de_tok(de_sentence)
                split_en_tok = en_tok(en_sentence)
                if a[i]:
                    de_swap = swap_sentence(split_de_tok, DE_NEUT_MAPPING, de_detok, entity=a[i][0])
                else:
                    de_swap = swap_sentence(split_de_tok, DE_NEUT_MAPPING, de_detok)
                en_swap = swap_sentence(split_en_tok, EN_NEUT_MAPPING, en_detok, startswith=False)
                print("{}\t{}".format(en_swap, de_swap))

