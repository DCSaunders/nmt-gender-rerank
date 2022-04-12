# nmt-gender-rerank
Scripts and nbest lists for our paper [First the worst: Finding better gender translations during beam search](https://arxiv.org/abs/2104.07429) (Findings of ACL 2022) 

## Abstract 

Neural machine translation inference procedures like beam search generate the most likely output under the model. This can exacerbate any demographic biases exhibited by the model. We focus on gender bias resulting from systematic errors in grammatical gender translation, which can lead to human referents being misrepresented or misgendered. 

Most approaches to this problem adjust the training data or the model. By contrast, we experiment with simply adjusting the inference procedure. We experiment with reranking nbest lists using gender features obtained automatically from the source sentence, and applying gender constraints while decoding to improve nbest list gender diversity. We find that a combination of these techniques allows large gains in WinoMT accuracy without requiring additional bilingual data or an additional NMT model.


## Requirements
* fast_align (Dyer et al 2013) https://github.com/clab/fast_align must be built and an environment variable FAST_ALIGN_BASE defined that points to its root directory, e.g.:
```
export FAST_ALIGN_BASE=/<...>/fast_align
```
* Python package mosestokenizer.

* Spacy and DeMorphy are required for Spanish and German evaluation. Experiments in paper conducted with spacy version 3.1.3.

## Example use
```
./rerank_nbest.sh LANG WDIR NBEST-LIST TAGGED-SOURCE 1BEST-OUTPUT-FILE
```
* LANG: two-letter abbreviation for target language. Current implementation supports de, he, es.

* WDIR: 	    a working directory where fastalign files will be output. Directory will be created if it does not exist.
* NBEST-LIST: 	    a file containing an nbest list in the target language, consisting of three columns with a triple-pipe ("|||") 
	    	    delimiter. First column contains sentence index, second column contains target-language hypotheses, 
		    third column contains score (higher is better)
* TAGGED-SOURCE:    a file containing three tab-delimited columns conveying gender information about the source sentence. 
  		    first column contains gender to search for. second column contains the entity - the word to identify gender for,
		    which may be provided as oracle information or identified by automatic coreference resolution.
		    The entity may contain multiple words (e.g. "the doctor" or "all teachers").
		    There may also be multiple entities per sentence, which should be pipe-separated (e.g. "the doctor|who".
		    Third column contains source sentence (which should be detokenized - it is tokenized internally).
* 1BEST-OUTPUT-FILE: Path to where the 1-best reranked selection (text only) should be output


The following command reranks the provided English-Spanish gender-constrained 20-best list using oracle entities.
 
```
./rerank_nbest.sh es tmp  nbest-lists/enes.constrainnbest.20  tagged-source/winomt-en-entity tmp/output.winomt.enes.20.constrain.rerank.oracle
```

## Citing
If you found the data or scripts here useful, please cite the paper:

```
@InProceedings{saunders-etal-2022-first,
  author    = {Saunders, Danielle and Sallis, Rosie and Byrne, Bill},
  title     = {First the worst: Finding better gender translations during beam search},
  booktitle = "Findings of the Association for Computational Linguistics: ACL 2022",
  month     = {May},
  year      = {2022},
  publisher = {Association for Computational Linguistics}
}
```