"""
    PivotAlign: A system for inducing bilingual dictionaries
    from parallel texts and pre-existing dictionaries for other language pairs.
    Script for creating a list of word pairs from Pharaoh-formatted word alignment system output
    Copyright (C) 2021 Steinþór Steingrímsson.
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"

import argparse
import math

parser = argparse.ArgumentParser(description='Takes a bilingual lexicon with frequencies and the source and target text files and prints the co-occurrences. Prints to stdout')
parser.add_argument('word_freq_list',
                    help='path to word freq list file with format: SOURCE_WORD\\tTARGET_WORD\\tFREQUENCY')
parser.add_argument('cooc_list',
                    help='path to co-occurrence list')
parser.add_argument('--out-file',
                    help='optional output file, otherwise prints to stdout')
parser.add_argument('--cutoff',
                    help='minimum number of co-occurrences')
parser.add_argument('--corpus-size',
                    help='minimum number of co-occurrences')
args = parser.parse_args()

wfl = open(args.word_freq_list).readlines()
cooc = open(args.cooc_list).readlines()
cutoff = 1
if args.cutoff:
    cutoff = args.cutoff

corpus_size = 1000000
if args.corpus_size:
    corpus_size = args.corpus_size

smoothing_term = math.log2(corpus_size)

cooc_dict = {}
ctr = 0
for line in cooc:
    current = line.strip().split('\t')
    src = current[0]
    trg = current[1]
    coocs = current[2]

    if src not in cooc_dict.keys():
        cooc_dict[src] = {}
    cooc_dict[src][trg] = coocs

    ctr += 1
    if (ctr % 100000 == 0):
        print(ctr)

ctr = 0
with open(args.out_file, 'w') as of:
    for line in wfl:
        try:
            src_word = line.split()[0]
            trg_word = line.split()[1]
            matches = line.split()[2]
            if int(matches) > int(cutoff):
                try:
                    coc = cooc_dict[src_word][trg_word]
                except Exception as e:
                    pass

            smoothed = float(int(matches)/(int(coc) + smoothing_term))
            of.write(str(src_word) + '\t' + str(trg_word) + '\t' + str(matches) + '\t' + str(coc) + '\t' + str(smoothed) + '\n')

            ctr += 1
            if (ctr % 10000 == 0):
                print(ctr)
        except Exception as e:
            print(line)
            print(e)
