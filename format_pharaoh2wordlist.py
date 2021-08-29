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

from collections import Counter
import argparse

parser = argparse.ArgumentParser(description='Takes a pharaoh alignment file and the source and target text files and prints the wordlist with frequency. Prints to stdout')
parser.add_argument('pharaoh_file',
                    help='path to pharaoh alignments file')
parser.add_argument('src_file',
                    help='path to source language text file')
parser.add_argument('trg_file',
                    help='path to target language text file')
parser.add_argument('--out-file',
                    help='optional output file, otherwise prints to stdout')
args = parser.parse_args()

# opening required input files
a = open(args.pharaoh_file)
s = open(args.src_file)
t = open(args.trg_file)
if args.out_file:
    o = open(args.out_file, 'w')

a_lines = a.readlines()
src_lines = s.readlines()
trg_lines = t.readlines()


ls =[]

lines = zip(a_lines, src_lines, trg_lines)
print('Reading the files now')
ctr = 0
for a_line, src_line, trg_line in lines:
    ctr += 1
    if a_line.lstrip().find('#####ERROR#####') < 0:   # skips the lines that have this specific error tag
        aligns = a_line.split()
        for align in aligns:
            try:
                src = align.split('-')[0]
                trg = align.split('-')[1]
                ls.append((src_line.split()[int(src)], trg_line.split()[int(trg)]))
            except:
                print(ctr)
                print(a_line)

print('Finished reading the file')

print('Tallying frequencies')
counts = Counter(ls)
if args.out_file:
    for pair in counts:
        out_string = str(pair[0]) + '\t' + str(pair[1]) + '\t' + str(counts[pair]) + '\n'
        o.write(out_string)
else:
    for pair in counts:
        print(str(pair[0]) + '\t' + str(pair[1]) + '\t' + str(counts[pair]))
