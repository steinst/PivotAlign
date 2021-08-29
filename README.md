PivotAlign
==============
A system participating in the TIAD 2021 shared task. PivotAlign induces a bilingual dictionary from the Apertium graph of dictionaries, using word alignments as a scoring mechanism.

Requirements
--------
- CombAlign (or other word alignment system)

Usage
--------
In order to run the system, you need `parallel corpora` and the `Apertium dictionaries` or other dictionaries in the same format. I have made the parallel corpora I used in the TIAD 2021 shared task available for [download](https://www.dropbox.com/sh/8i0q2iphmdre1m4/AADr4OYyhUZP_TmDPilcfRsOa?dl=0). The apertium dictionaries are available [here](https://tiad2021.unizar.es/data/TransSets_ApertiumRDFv2_1_CSV.zip).  

We assume you place the parallel corpora under `PivotAlign/parallel` and the Apertium dictionaries under `PivotAlign/Apertium`. The corpora have been tokenized and lemmatized using SpaCy.

When the data is in place, run the following:

#### Create co-occurrence lists from the parallel corpora
```
python3 create_cooc_list.py parallel/lemmatized/[src]_[trg].million.parallel.[src].lem parallel/lemmatized/[src]_[trg].million.parallel.[trg].lem --out-file working/[src]_[trg].cooc
```
Replace `[src]` with code for the source language you are working with and `[trg]` with the target language. For example, if working with English and French, you would replace `[src]` with `en` and `[trg]` with `fr`.

#### Do word alignments
Follow instructions for [CombAlign](https://github.com/steinst/CombAlign) or other word alignment tool. You want the output to be in Pharaoh-format:

```
9-15 4-8 1-2 11-15 0-0 12-16 10-9 3-5 5-7 8-14 2-3 7-12
2-4 4-6 1-2 1-0 0-1 0-3 3-5 5-7
7-10 1-2 9-11 5-4 7-6 8-10 0-0 1-1 3-3 6-7 2-2 10-12 6-5
7-10 4-3 1-0 5-4 7-6 8-11 6-9 4-1 0-2 2-2 6-5
8-6 4-5 0-1 5-3 0-0 7-0 2-1 3-2 6-4
12-15 4-8 1-2 2-5 10-13 4-4 13-16 3-6 3-7 3-4 0-0 8-9 5-7 6-8 11-14 2-3 7-8 9-12
2-4 3-6 5-8 4-7 1-3 0-1 0-0 3-5
```
Each line represents one sentence and pair of numbers represents an aligned SRC-TRG word pair.

Save the alignments in the `alignments/` folder.
[Pharaoh format]

#### Word alignments to word lists
```
python3 format_pharaoh2wordlist.py alignments/[src]_[trg].alignments parallel/lemmatized/[src]_[trg].million.parallel.[src].lem parallel/lemmatized/[src]_[trg].million.parallel.[trg].lem --out-file working/[src]_[trg]_wordlist.txt
```

#### Calculate word alignment score
```
python3 wordlist2wordrels_new.py working/[src]_[trg]_wordlist.txt working/[src]_[trg].cooc --out-file working/[src]_[trg]_wordlist_scores.txt
```

#### Create candidate lists by pivoting through the Apertium dictionaries
```
python3 pivot_apertium.py
```

#### Filter and output data, calculate precision, recall and F1
```
python3 filter_and_calculate_scores.py en-fr
```

Citation
-------
If you use or discuss PivotAlign in published research, please cite the paper:
```
@inproceedings{pivotalign-tiad2021,
  author    = {Steingrímsson, Steinþór  and  Loftsson, Hrafn  and  Way, Andy},
  title     = {PivotAlign: Leveraging High-Precision Word Alignments for Bilingual Dictionary Inference},
  booktitle = {Proceedings of TIAD-2021 Shared Task – Translation Inference Across Dictionaries
co-located with the 4th Language, Data and Knowledge Conference (LDK 2021)},
  month     = {September},
  year      = {2021},
  address   = {Zaragoza, Spain},
}
```

License
-------

Copyright (C) 2021, Steinþór Steingrímsson

Licensed under the terms of the Apache License, version 2.0. A full copy of the license can be found in LICENSE.
