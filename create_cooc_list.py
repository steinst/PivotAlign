"""
    PivotAlign: A system for inducing bilingual dictionaries
    from parallel texts and pre-existing dictionaries for other language pairs.
    Script for creating co-occurrence lists from parallel corpora
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

parser = argparse.ArgumentParser(description='Takes a parallel corpora and prints word co-occurrences. Prints to stdout')
parser.add_argument('src_file',
                    help='path to source language text file')
parser.add_argument('trg_file',
                    help='path to target language text file')
parser.add_argument('--out-file',
                    help='optional output file, otherwise prints to stdout')
parser.add_argument('--cutoff',
                    help='minimum number of co-occurrences')
args = parser.parse_args()

src_lines = open(args.src_file).readlines()
trg_lines = open(args.trg_file).readlines()
cutoff = 1
if args.cutoff:
    cutoff = args.cutoff

no_lines = len(src_lines)
ctr = 0
cooc_dict = {}
while ctr < no_lines:
    src_line = set(src_lines[ctr].split())
    trg_line = set(trg_lines[ctr].split())
    for src_word in src_line:
        if src_word not in cooc_dict.keys():
            cooc_dict[src_word] = {}
        for trg_word in trg_line:
            if trg_word in cooc_dict[src_word].keys():
                cooc_dict[src_word][trg_word] += 1
            else:
                cooc_dict[src_word][trg_word] = 1
    ctr += 1
    if (ctr % 1000 == 0):
        print(ctr)

with open(args.out_file, 'w') as of:
    for src_words in cooc_dict.keys():
        for trg_words in cooc_dict[src_words].keys():
            if cooc_dict[src_words][trg_words] > int(cutoff):
                of.write(str(src_words) + '\t' + str(trg_words) + '\t' + str(cooc_dict[src_words][trg_words]) + '\n')
