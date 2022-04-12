# coding=utf-8
from __future__ import print_function
from mosestokenizer import *
import sys
from pprint import pprint
import ast
import codecs
from demorphy import Analyzer
import spacy
from args import args
analyzer = Analyzer(char_subs_allowed=True)

tokenizers = {"he": MosesTokenizer("en"),
              "en": MosesTokenizer("en"),
              "de": MosesTokenizer("de"),
              "es": MosesTokenizer("es")}
# follows morphological analysis approach in Stanovsky et al (2019): predetermined rules for he, spacy/demorphy for es and de

SRC_ARTICLES = set(["the", "a", "an"])
NEUTRAL_PLACEHOLDERS = set(["DEFNOM", "DEFACC", "DEFDAT", "DEFGEN", "PRONNOM"])
NEUTRAL_PLACEHOLDERS_STARTSWITH = set(["PRONPOS", "PRONOBL"])
NEUTRAL_PLACEHOLDERS_ENDSWITH = set(["NEND"])
spacy_genders = {"Masc": "male", "Fem": "female", "Neut": "neutral"}
lang_cache = {}


def try_get_de_gender(tok):
    for case in tok:
        if case.__contains__("fem"):
            return("female")
        if case.__contains__("masc"):
            return("male")
    return None
        

def neutral_check(entity, genders):
    if entity in NEUTRAL_PLACEHOLDERS:
        genders.append("neut")
    else:
        for p in NEUTRAL_PLACEHOLDERS_STARTSWITH:
            if entity.startswith(p):
                genders.append("neut")
                break
        if not genders:
            for p in NEUTRAL_PLACEHOLDERS_ENDSWITH:
                if entity.endswith(p):
                    genders.append("neut")
                    break
        

class TargetHypothesis:
    alignments = {}

    def __init__(self, detok_sentence, log_lik, lang):
        self.detok_sentence = detok_sentence
        self.log_lik = log_lik
        self.lang = lang
        self.gender_correct_frac = 0.0
        self.tokens = tokenizers[self.lang](detok_sentence)
        self.tok_sentence = self.tokens
        if self.tok_sentence:
            self.tok_sentence[0] = self.tok_sentence[0].lower()
        self.tok_sentence = " ".join(self.tok_sentence)

    def __repr__(self):
        return self.detok_sentence + "\n"

    def __lt__(hyp1, hyp2):
        if hyp1.gender_correct_frac != hyp2.gender_correct_frac:
            return hyp1.gender_correct_frac < hyp2.gender_correct_frac
        else:
            return hyp1.log_lik < hyp2.log_lik



    def get_mapped_genders(self, src_indices, nlp=None):
        mapped_genders = []
        morph = None
        if nlp:
            morph = nlp(self.tok_sentence)
        for src_index in src_indices:
            gender = "unknown"
            if src_index in self.alignments:
                target_index = self.alignments[src_index]
                entity = self.tokens[target_index]
                if morph:
                    entity = morph[target_index]
                if entity in lang_cache:
                    gender = lang_cache[entity]
                # GERMAN
                if self.lang == "de":
                    genders = []
                    neutral_check(str(entity), genders)
                    if not genders:
                        case = entity.morph.get("Case")
                        morphy_check = analyzer.analyze(str(entity))
                        if len(case) > 0:
                            case = case[0].lower()
                            genders = [d.gender for d in morphy_check if d.case == case]
                        else:
                            genders = [d.gender for d in morphy_check]
                    # need following because same token may have multiple possible genders listed in morphy
                    mcount = genders.count("masc")
                    fcount = genders.count("fem")
                    ncount = genders.count("neut") 
                    all_count = [mcount, fcount, ncount]
                    if sum(all_count) > 0:
                        if max(all_count) == mcount:
                            gender = "male"
                        elif max(all_count) == fcount:
                            gender = "female"
                        elif max(all_count) == ncount:
                            gender = "neutral"
                elif self.lang == "es":
                    morph_info = entity.morph.get("Gender")
                    if len(morph_info) > 0:
                        gender = spacy_genders[morph_info[0]]
                # HEBREW
                elif self.lang == "he":
                    if entity != "את" and entity[-1] in  ["ת" , "ה"]:
                        gender = "female"
                    else:
                        gender = "male"
                #if entity not in lang_cache:
                #    lang_cache[entity] = gender
            mapped_genders.append(gender)
        self.mapped_genders = mapped_genders


class Source:
    def __init__(self, detok_sentence, gold_gender, gold_entity):
        self.detok_sentence = detok_sentence
        self.gold_gender = gold_gender
        self.gold_entity = gold_entity.split("|")
        self.hypotheses = []
        self.tokens = None
        self.tok_sentence = None 
        self.src_indices = []
        self.make_tok(detok_sentence)
        for e in self.gold_entity:
            self.get_src_indices(e)

    def make_tok(self, detok_sentence):
        self.tokens = tokenizers["en"](detok_sentence)
        self.tok_sentence = " ".join(self.tokens)

    def __repr__(self):
        result = ""
        for hyp in self.hypotheses:
            result += "{0} ||| {1}\n".format(self.tok_sentence, hyp.tok_sentence)
        return result

    def get_src_indices(self, entity):
        # finding indices in tokenized source sentence for source entities (may be more than one word)
        split_src = self.tok_sentence.split(entity)
        entity_len = len(entity.split())
        last_w = ""
        if len(split_src) > 1:
            last_segment = split_src[0].split()
            prev_len = len(last_segment)
            for i in range(1, len(split_src)):
                if len(last_segment) > 0:
                    last_w = last_segment[-1]
                if last_w.lower() in SRC_ARTICLES:
                    self.src_indices.append(prev_len - 1)
                for l in range(entity_len):
                    self.src_indices.append(prev_len + l)
                last_segment = split_src[i].split()
                prev_len += entity_len + len(last_segment)

                
    def compare_with_gold(self):
        for i, hyp in enumerate(self.hypotheses):
            non_unknown = [g for g in hyp.mapped_genders if g != "unknown"]
            if len(non_unknown) > 0:
                correct = [g for g in non_unknown if g == self.gold_gender]
                hyp.gender_correct_frac =  len(correct) / len(non_unknown)
            # Naive approach requires all aligned known grammatical gender correct
            #if all([g == self.gold_gender for g in hyp.mapped_genders if g != "unknown"]):
            #    hyp.is_gender_correct = True
                

def parse_nbest(nbest, tagged_source, lang):
    """
    Constructs source objects from a tagged source file and populates with hypotheses from nbest
    Expects tagged source to be in winomt format: gender, gendered entity index, sentence
    Returns list of Source objects
    """
    source_list = []

    with codecs.open(tagged_source, encoding='utf-8') as fin:
        for line in fin:
            split_line = line.split("\t")
            gold_gender = split_line[0]
            gold_entity = split_line[1]
            sentence = split_line[2].strip() 
            source_list.append(Source(sentence, gold_gender, gold_entity))

    with codecs.open(nbest, encoding='utf-8') as fin:
        for line in fin:
            raw_index, raw_sentence, raw_likelihood = line.split("|||")
            index = int(raw_index.strip())
            sentence = raw_sentence.strip()
            log_lik = float(raw_likelihood.strip())
            new_hyp = TargetHypothesis(sentence, log_lik, lang)
            if source_list[index].gold_entity in ("ROBERTA-NO-TAG", "ROBERTA-TAG-EXCEPTION"):
                if (not source_list[index].hypotheses) or (log_lik > source_list[index].hypotheses[0].log_lik):
                    source_list[index].hypotheses = [new_hyp]
            else:
                source_list[index].hypotheses.append(new_hyp)
    return source_list


def convert_alignments_dict(string):
    """
    Makes a dictionary of key = source index : value = target index (from the output text from fast align).
    """
    string = "{" + string + "}"
    string = string.replace("-", ":")
    string = string.replace(" ", ",")
    my_dict = ast.literal_eval(string)
    return my_dict


def parse_alignments(alignments_filename, source_list, lang):
    """
    Loads alignment output file into the Source and TargetHypothesis objects. 
    Determines whether each hypothesis is gender-consistent with the source gender annotations.
    """ 
    nlp = None
    if lang != "he":
        nlp = spacy.load("{}_core_news_sm".format(lang))
    with open(alignments_filename, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        counter = 0
        for source in source_list:
            for hyp in source.hypotheses:
                this_alignment = lines[counter]
                hyp.alignments = convert_alignments_dict(this_alignment)
                hyp.get_mapped_genders(source.src_indices, nlp)
                counter += 1
            source.compare_with_gold()


def write_best_hyp_to_file(source_list, filename):
    """
    Creates file with the 'best' hypothesis choice for each source sentence.
    """
    with codecs.open(filename, "w", encoding='utf-8') as f:
        f.writelines(repr(max(source.hypotheses)) for source in source_list)



if __name__ == "__main__":
    source_list = parse_nbest(args.nbest, args.tagged_source, args.lang)
    parse_alignments('{}/fast_align_output'.format(args.outdir), source_list, args.lang)
    write_best_hyp_to_file(source_list, args.outfile)


