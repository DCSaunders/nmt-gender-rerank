from __future__ import print_function, division
import sys
import random
import collections


class Sample(object):
    def __init__(self, idx, entity, entity_idx):
        self.idx = idx + 3888
        self.entity = entity
        self.gender = "neutral"
        self.entity_idx = entity_idx
        self.total_m_score = 0
        self.en = None
        self.m_hyps = []
        self.n_hyps = []

    def add_m_hyp_line(self, hyp, score):
        s = float(score.strip())
        self.total_m_score += s
        self.m_hyps.append((hyp.strip(), s))

    def shuffle_in(self, max_hyps=20):
        num_m = min(max_hyps - len(self.n_hyps), len(self.m_hyps))
        av_score = self.total_m_score / len(self.m_hyps)
        for idx in range(len(self.n_hyps)):
            self.n_hyps[idx] = (self.n_hyps[idx], av_score)
        for i in range(num_m):
            self.n_hyps.append(self.m_hyps[i])

#output files
out_tags = "en_neutral_tags.out"
out_nbest = "nbest_withneutral.out"

#input files
neutral_primary = "de_neutral_primary.out"
neutral_secondary = "de_neutral_secondary.out"
neutral_en = "en_neutral.out"
tags = "mt_gender/data/aggregates/en.txt" 
nbest = "nbest.winomt.ende.20.constrain"

max_hyps=20
# go through tags, save samples
new_samples = dict()
found = 0
order_to_idx = dict()
with open(tags) as f:
    for idx, line in enumerate(f):
        gender, entity_idx, _, entity = line.split("\t")
        if gender == "male":
            new_samples[idx] = Sample(found, entity, entity_idx)
            order_to_idx[found] = idx # map order found to "real" id
            found += 1

with open(nbest) as f:
    for line in f:
        idx, hyp, score = [x.strip() for x in line.strip().split("|||")]
        idx = int(idx)
        if idx in new_samples:
            new_samples[idx].add_m_hyp_line(hyp, score)

with open(neutral_primary) as f1, open(neutral_secondary) as f2:
    for idx, (l1, l2) in enumerate(zip(f1, f2)):
        real_id = order_to_idx[idx]
        new_samples[real_id].n_hyps.append(l1.strip())
        #new_samples[real_id].n_hyps.append(l2.strip())


with open(out_tags, "w") as ftagsout, open(out_nbest, "w") as fnbestout, open(neutral_en) as fneut:
    for idx, line in enumerate(fneut):
        real_id = order_to_idx[idx]
        sample = new_samples[real_id]
        sample.shuffle_in(max_hyps)
        ftagsout.write("neutral\t{}\t{}\t{}".format(sample.entity_idx, line.strip(), sample.entity))
        for hyp, score in sample.n_hyps:
            fnbestout.write("{} ||| {} ||| {}\n".format(sample.idx, hyp, score))
