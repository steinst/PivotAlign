#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    PivotAlign: A system for inducing bilingual dictionaries
    from parallel texts and pre-existing dictionaries for other language pairs.
    Script for filtering candidate lists and calculating precision, recall and F1.
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

#TODO: Some adaption unfinished for final published version.

# Get translations sets through pivoting
# Pairs: en/fr fr/pt pt/en

# One pivot for en/fr:
# en/eo - eo/fr; en-es - es/fr; en/ca - ca/fr
import sys
import itertools

transset_folder = "Apertium/"
working_folder = "working/"

val_pair = sys.argv[1]
pivot_set = sys.argv[2]
method = sys.argv[3]

src_lang, trg_lang = val_pair.split('-')

val_dict_src = {}

outfile = working_folder + src_lang + '_' + trg_lang + '_' + pivot_set + '_wordlist_scores.' + method + '.txt'

alignment_dict = {}
alignment_scores = {}
with open(transset_folder + src_lang + '_' + trg_lang + '_wordlist_scores.' + method + '.txt', 'r') as alignments:
    for i in alignments:
        temp = i.strip().split('\t')
        src_word = temp[0]
        trg_word = temp[1]
        count = temp[2]
        score = temp[4]
        if src_word in alignment_dict.keys():
            alignment_dict[src_word].append(trg_word)
            alignment_scores[src_word][trg_word + '_score'] = float(score)
            alignment_scores[src_word][trg_word + '_count'] = int(count)
        else:
            alignment_dict[src_word] = [trg_word]
            alignment_scores[src_word] = {trg_word + '_score': float(score), trg_word + '_count': int(count)}
print(len(alignment_dict.keys()))


with open(transset_folder + 'validation/ValidationData_' + val_pair + '.tsv','r') as vin:
    for i in vin:
        temp = i.strip().split('\t')
        try:
            val_dict_src[temp[0] + '__' + temp[2]].append(temp[1] + '__' + temp[2])
        except:
            val_dict_src[temp[0] + '__' + temp[2]] = [temp[1] + '__' + temp[2]]

src_dict = {}
with open(transset_folder + 'apertium/test_max3edges_' + pivot_set + '_' + src_lang + '_' + trg_lang + '.txt', 'r') as sin:
    for i in sin:
        try:
            temp = i.strip().split('\t')
            src_rep = temp[0]
            trg_rep = temp[1]
            pos = temp[4].strip('"').split('#')[1]

            try:
                src_dict[src_rep + '__' + pos].append(trg_rep + '__' + pos)
            except:
                src_dict[src_rep + '__' + pos] = [trg_rep + '__' + pos]
        except Exception as e:
            print(e)
print(len(src_dict.keys()))

recall = 0
total_val = 0
precision = 0
total_src = 0

new_src_dict = {}
output_dict = {}
done_dict = []
for i in src_dict.keys():
    ii = i.split('__')[0]
    if ii in alignment_dict.keys():
        for j in src_dict[i]:
            trg_word = j.split('__')[0]
            if trg_word in alignment_dict[ii]:
                if ((alignment_scores[ii][trg_word + '_score'] > 0.12)
                        #or ((alignment_scores[ii][trg_word + '_count'] > 50) and (alignment_scores[ii][trg_word + '_score'] > 0.7))
                        #or ((alignment_scores[ii][trg_word + '_count'] > 165) and (
                        #        alignment_scores[ii][trg_word + '_score'] > 0.6))
                        #or ((alignment_scores[ii][trg_word + '_count'] > 75) and (
                        #        alignment_scores[ii][trg_word + '_score'] > 0.65))
                        #or ((alignment_scores[ii][trg_word + '_count'] > 300) and (
                        #        alignment_scores[ii][trg_word + '_score'] > 0.15))
                        #or ((alignment_scores[ii][trg_word + '_count'] > 400) and (
                        #        alignment_scores[ii][trg_word + '_score'] > 0.33))
                        #or ((alignment_scores[ii][trg_word + '_count'] > 250) and (
                        #        alignment_scores[ii][trg_word + '_score'] > 0.05))
                ):
                    if i.find(' ') < 0:
                        if j.find(' ') < 0:
                            if (i + '_' + j) not in done_dict:
                                if i in output_dict.keys():
                                    targets = src_dict[i]
                                    for trgs in targets:
                                        if trgs == j:
                                            trg, pos = trgs.split('__')
                                            score = alignment_scores[ii][trg + '_score']
                                            if score > 1:
                                                score = 1
                                            output_dict[i].append([trg, pos, str(score)])
                                            output_dict[i] = list(output_dict[i] for output_dict[i], _ in itertools.groupby(output_dict[i]))
                                else:
                                    targets = src_dict[i]
                                    for trgs in targets:
                                        if trgs == j:
                                            trg, pos = trgs.split('__')
                                            score = alignment_scores[ii][trg + '_score']
                                            if score > 1:
                                                score = 1
                                            output_dict[i] = [[trg, pos, str(score)]]
                                            output_dict[i] = list(output_dict[i] for output_dict[i], _ in itertools.groupby(output_dict[i]))

                                if i in new_src_dict.keys():
                                    new_src_dict[i].append(j)
                                else:
                                    new_src_dict[i] = [j]
                                done_dict.append(i + '_' + j)

with open(outfile + '.F', 'w') as fo:
    for i in output_dict.keys():
        for j in output_dict[i]:
            fo.write(i.split('__')[0] + '\t' + str(j[0]) + '\t' + str(j[1]) + '\t' + str(j[2]) + '\n')
#new_src_dict = src_dict
val_keys = 0
for i in val_dict_src.keys():
    val_keys += 1
    if i in new_src_dict.keys():
        for j in val_dict_src[i]:
            if j in new_src_dict[i]:
                recall += 1
            total_val += 1
    else:
        for j in val_dict_src[i]:
            total_val += 1

coverage_keys = 0
for i in new_src_dict.keys():
    if i in val_dict_src.keys():
        coverage_keys += 1
        for j in new_src_dict[i]:
            if j in val_dict_src[i]:
                precision += 1
            total_src += 1

coverage = float(coverage_keys / val_keys)
print('coverage: ', str(coverage))

recall_score = float(recall/total_val)
try:
    precision_score = float(precision/total_src)
except:
    precision_score = 0.0
try:
    f_score = (2 * recall_score * precision_score) / (recall_score + precision_score)
except:
    f_score = 0.0
print('recall     : ' + str(recall) + ' af ' + str(total_val))
print('-------------------------------------')
print('precision     : ' + str(precision) + ' af ' + str(total_src))
print('P: ' + str(precision_score))
print('R: ' + str(recall_score))
print('F1: ' + str(f_score))