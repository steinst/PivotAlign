#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    PivotAlign: A system for inducing bilingual dictionaries
    from parallel texts and pre-existing dictionaries for other language pairs.
    Script for pivoting through the Apertium dictionaries to create a candidate list
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
import multiprocessing
import sys
from os import path
import itertools
import os
import time
from collections import Counter
from queue import Queue
from threading import Thread
from threading import Lock
from multiprocessing import Process, Manager

transset_folder = "/home/steinst/tiad2021/"
dict_of_dicts = Manager().dict()
dict_of_lists = {}

syn_ratio_threshold = 0.4

synonyms = {}

## Gera lúppu sem fer í gegnum öll pörin
## Eftir að öll pörin eru komin, pivota þá í gegnum lokapörin
## Keyra svo út niðurstöður (með POS-tagi líka)
##
## Samþykkja öll proper nouns? skor=1 ? (eða skor = 1 þar sem þau eru nákvæmlega eins skrifuð)
## samþykkja öll alignment sem finnast og setja skor á þau
## ef öðrumegin er mwe, greppa þá stóru parallel-skrána og samþykkja það sem finnst: skor=1

pathway = sys.argv[1]
addsynonym = int(sys.argv[2])
pos_dict = {}

accepted_dict = {}
suggestions_dict = {}

def create_pair_dict(src, trg):
    src_trg_dict = {}
    trg_src_dict = {}
    src_list = []
    trg_list = []
    pair_name = 'TransSet' + src.upper() + '-' + trg.upper() + '.csv'
    if not path.exists(transset_folder + pair_name):
        pair_name = 'TransSet' + trg.upper() + '-' + src.upper() + '.csv'
    with open(transset_folder + pair_name, 'r') as pair_in:
        for line in pair_in:
            if not line.lstrip().startswith('"written_rep_a"'):
                try:
                    line_list = line.strip().split('" , "')
                    src_rep = line_list[0].lstrip('"')
                    trg_rep = line_list[6]
                    src_entry = line_list[1] + '__' + src_rep
                    trg_entry = line_list[5] + '__' + trg_rep
                    POS = line_list[7].strip().strip(" ,")
                    pos_dict[src_entry] = POS
                    pos_dict[trg_entry] = POS

                    src_list.append(src_entry)
                    trg_list.append(trg_entry)

                    if src_entry in src_trg_dict.keys():
                        src_trg_dict[src_entry].append([src_rep, trg_entry, trg_rep, POS])
                    else:
                        src_trg_dict[src_entry] = [[src_rep, trg_entry, trg_rep, POS]]
                    if trg_entry in trg_src_dict.keys():
                        trg_src_dict[trg_entry].append([trg_rep, src_entry, src_rep, POS])
                    else:
                        trg_src_dict[trg_entry] = [[trg_rep, src_entry, src_rep, POS]]
                except Exception as e:
                    pass
        src_list = list(set(src_list))
        trg_list = list(set(trg_list))
    return src_trg_dict, trg_src_dict, src_list, trg_list


def pivot(*pairs):
    first_dict = True
    out_dict = {}
    for pair in pairs:
        if first_dict:
            previous_dict = dict_of_dicts[pair]
            out_dict = previous_dict.copy()
            first_dict = False
        else:
            working_dict = dict_of_dicts[pair]
            out_dict = {}
            for key in previous_dict.keys():
                trans_list = previous_dict[key]
                for t in trans_list:
                    translation = t[1]
                    try:
                        #print(translation)
                        pivot_translation = working_dict[translation]
                        for pt in pivot_translation:
                            if key in out_dict.keys():
                                out_dict[key].append(pt)
                            else:
                                out_dict[key] = [pt]
                    except:
                        pass
        previous_dict = out_dict.copy()
    return out_dict


def pivot_path(path_dict):
    pivot_paths = path_dict.keys()
    for pivots in pivot_paths:
        print('pivoting ' + pivots)
        src_lang, trg_lang = pivots.split('_')
        out_list = []
        for curr_pivot in path_dict[pivots]:
            curr_dict = pivot(*curr_pivot)
            for key in curr_dict.keys():
                translations = curr_dict[key]
                for i in translations:
                    word = key.split('__')[1]
                    out_list.append(word + '\t' + i[2] + '\t' + key + '\t' + i[1] + '\t' + i[3] + '\n')
        out_list = list(set(out_list))

        try:
            temp_src = dict_of_dicts[src_lang + '_' + trg_lang].copy()
        except:
            temp_src = {}

        try:
            temp_trg = dict_of_dicts[trg_lang + '_' + src_lang].copy()
        except:
            temp_trg = {}

        for i in out_list:
            src_rep, trg_rep, src_entry, trg_entry, POS = i.strip().split('\t')

            src_key = src_entry # + '__' + src_rep
            trg_key = trg_entry # + '__' + trg_rep
            if src_key in temp_src.keys():
                temp_src[src_key].append([src_rep, trg_entry, trg_rep, POS])
                temp_src[src_key].sort()
                temp_src[src_key] = list(temp_src[src_key] for temp_src[src_key], _ in itertools.groupby(temp_src[src_key]))
            else:
                temp_src[src_key] = [[src_rep, trg_entry, trg_rep, POS]]
            if trg_key in temp_trg.keys():
                temp_trg[trg_key].append([trg_rep, src_entry, src_rep, POS])
                temp_trg[trg_key].sort()
                temp_trg[trg_key] = list(temp_trg[trg_key] for temp_trg[trg_key],_ in itertools.groupby(temp_trg[trg_key]))
            else:
                temp_trg[trg_key] = [[trg_rep, src_entry, src_rep, POS]]
        dict_of_dicts[src_lang + '_' + trg_lang] = temp_src.copy()
        dict_of_dicts[trg_lang + '_' + src_lang] = temp_trg.copy()

def pivot_path_dict():

    # Add synonym lookup
    while True:
        try:
            pivots, path_dict = q.get()
            print('pivoting ' + pivots)
            src_lang, trg_lang = pivots.split('_')
            out_list = []
            for curr_pivot in path_dict[pivots]:
                print(curr_pivot)
                curr_dict = pivot(*curr_pivot)
                for key in curr_dict.keys():
                    translations = curr_dict[key]
                    for i in translations:
                        word = key.split('__')[1]
                        out_list.append(
                            word + '\t' + i[2] + '\t' + key + '\t' + i[1] + '\t' + i[3] + '\n')
                        if addsynonym > 0:
                            try:
                                trans_syns = synonyms[i[1]]
                                for j in trans_syns:
                                    if pos_dict[j] == pos_dict[key]:
                                        word = j.split('__')[1]
                                        out_list.append(word + '\t' + i[2] + '\t' + j + '\t' + i[1] + '\t' + pos_dict[j] + '\n')
                            except:
                                pass
                            try:
                                source_syns = synonyms[key]
                                for j in source_syns:
                                    if pos_dict[j] == pos_dict[key]:
                                        word = j.split('__')[1]
                                        out_list.append(word + '\t' + i[2] + '\t' + j + '\t' + i[1] + '\t' + pos_dict[j] + '\n')
                            except:
                                pass

            out_list = list(set(out_list))

            try:
                temp_src = dict_of_dicts[src_lang + '_' + trg_lang].copy()
            except:
                temp_src = {}

            try:
                temp_trg = dict_of_dicts[trg_lang + '_' + src_lang].copy()
            except:
                temp_trg = {}

            for i in out_list:
                src_rep, trg_rep, src_entry, trg_entry, POS = i.strip().split('\t')

                src_key = src_entry #+ '__' + src_rep
                trg_key = trg_entry #+ '__' + trg_rep
                if src_key in temp_src.keys():
                    temp_src[src_key].append([src_rep, trg_entry, trg_rep, POS])
                    #temp_src[src_key] = list(set(temp_src[src_key]))
                    temp_src[src_key].sort()
                    temp_src[src_key] = list(temp_src[src_key] for temp_src[src_key], _ in itertools.groupby(temp_src[src_key]))
                else:
                    temp_src[src_key] = [[src_rep, trg_entry, trg_rep, POS]]
                if trg_key in temp_trg.keys():
                    temp_trg[trg_key].append([trg_rep, src_entry, src_rep, POS])
                    #temp_trg[trg_key] = list(set(temp_trg[trg_key]))
                    temp_trg[trg_key].sort()
                    temp_trg[trg_key] = list(temp_trg[trg_key] for temp_trg[trg_key], _ in itertools.groupby(temp_trg[trg_key]))
                else:
                    temp_trg[trg_key] = [[trg_rep, src_entry, src_rep, POS]]
            dict_of_dicts[src_lang + '_' + trg_lang] = temp_src.copy()
            dict_of_dicts[trg_lang + '_' + src_lang] = temp_trg.copy()
            q.task_done()
        except Queue.Empty:
            return


def get_lang_words(lang, *pairs):
    all_words_out = []
    for i in pairs:
        src, trg = i
        pair_name = 'TransSet' + src.upper() + '-' + trg.upper() + '.csv'
        with open(transset_folder + pair_name, 'r') as pair_in:
            for line in pair_in:
                if not line.startswith('"written_rep_a"'):
                    try:
                        line_list = line.strip().split('" , "')
                        src_rep = line_list[0].lstrip('"')
                        trg_rep = line_list[6]
                        src_entry = line_list[1]
                        trg_entry = line_list[5]
                        if lang == src:
                            all_words_out.append(src_entry)
                        else:
                            all_words_out.append(trg_entry)
                    except:
                        pass
    return all_words_out


def work_pair(p, dict_of_dicts):
        try:
            dict_a, dict_b, list_a, list_b = create_pair_dict(p[0], p[1])
            dict_of_dicts[p[0] + '_' + p[1]] = dict_a.copy()
            dict_of_dicts[p[1] + '_' + p[0]] = dict_b.copy()

            for a in list_a:
                try:
                    dict_of_lists[p[0]].append(a)
                except:
                    dict_of_lists[p[0]] = [a]
            dict_of_lists[p[0]] = list(set(dict_of_lists[p[0]]))

            for b in list_b:
                try:
                    dict_of_lists[p[1]].append(b)
                except:
                    dict_of_lists[p[1]] = [b]
            dict_of_lists[p[1]] = list(set(dict_of_lists[p[1]]))
            return
        except Exception as e:
            print(e)
            return


def att_otac(p, dict_of_dicts):
        try:
            otac_ctr = 0
            src_w = p[0]
            trg_w = p[1]
            o_pairs = pairs.copy()

            for o in o_pairs:
                if o[0] == src_w:
                    s_i = o[0] + '_' + o[1]
                    i_t = o[1] + '_' + trg_w
                    i_s = o[1] + '_' + o[0]
                    t_i = trg_w + '_' + o[1]
                elif o[1] == src_w:
                    s_i = o[1] + '_' + o[0]
                    i_s = o[0] + '_' + o[1]
                    i_t = o[0] + '_' + trg_w
                    t_i = trg_w + '_' + o[0]
                elif o[0] == trg_w:
                    i_t = o[1] + '_' + o[0]
                    t_i = o[0] + '_' + o[1]
                    s_i = src_w + '_' + o[1]
                    i_s = o[1] + '_' + src_w
                elif o[1] == trg_w:
                    s_i = src_w + '_' + o[0]
                    i_s = o[0] + '_' + src_w
                    i_t = o[0] + '_' + o[1]
                    t_i = o[1] + '_' + o[0]
                else:
                    continue

                try:
                    s_i_dict = dict_of_dicts[s_i].copy()
                    i_s_dict = dict_of_dicts[i_s].copy()
                    i_t_dict = dict_of_dicts[i_t].copy()
                    t_i_dict = dict_of_dicts[t_i].copy()
                    #print(p, o, 'inni')
                except:
                    continue

                out_dict = {}
                non_ec_dict = {}

                s_t = src_w + '_' + trg_w
                info_dict = {}
                temp_s_i_ctr = 0
                for s_i_key in s_i_dict.keys():
                    si_set = []
                    si_dict = {}
                    ti_set = []
                    tr_dict = {}
                    try:
                        temp_s_i_ctr += 1
                        #if temp_s_i_ctr % 5000 == 0:
                        #    print(s_t, str(temp_s_i_ctr), str(len(s_i_dict.keys())))

                        if True:
                            counter_list = []
                            trans_list = s_i_dict[s_i_key]
                            for si in trans_list:
                                s_rep, i_t_key, si_rep, si_pos = si
                                si_set.append(i_t_key)
                                si_dict[i_t_key] = {'s_rep': s_rep, 'si_rep': si_rep, 'si_pos': si_pos}
                            info_dict[s_i_key] = [s_rep, si_pos]

                            for it_list in si_set:
                                counter_dict = {}
                                one2oneFlag = False
                                try:
                                    it_set = []
                                    ti_set = []
                                    it_dict = {}
                                    inverse_list = i_t_dict[it_list]
                                    for it in inverse_list:
                                        i_rep, t_key, t_rep, it_pos = it
                                        it_set.append(t_key)
                                        it_dict[t_key] = {'i_rep': i_rep, 't_rep': t_rep, 'it_pos': it_pos}
                                        for ti in t_i_dict[t_key]:
                                            ti_set.append(ti[1])
                                            tr_dict[ti[1]] = {'t_rep': ti[0], 't_pos': ti[3]}
                                            if ti[1] in counter_dict.keys():
                                                counter_dict[ti[1]].append(t_key)
                                            else:
                                                counter_dict[ti[1]] = [t_key]
                                        #print(t_key)
                                        info_dict[t_key] = [ti[0], ti[3]]
                                        common = list(set(si_set).intersection(ti_set))
                                        for i in common:
                                            counter_list.append(i)
                                    if len(si_set) == len(it_set) == 1:
                                        one2oneFlag = True
                                        if si_dict[it_list]['si_pos'] == it_pos:
                                            if s_i_key in out_dict:
                                                out_dict[s_i_key].append(t_key)
                                            else:
                                                out_dict[s_i_key] = [t_key]


                                except:
                                    pass

                                if one2oneFlag == False:
                                    counted = Counter(counter_list)
                                    #print(counted)
                                    for ctd in counted.keys():
                                        if counted[ctd] > 0:
                                            trans_otic = []
                                            #print(counter_dict)
                                            for it in counter_dict.keys():
                                                for t_ot in counter_dict[it]:
                                                    #print(t_ot)
                                                    trans_otic.append(t_ot)
                                                    t_counted = Counter(trans_otic)
                                                    for t_out in t_counted:
                                                        if t_counted[t_out] > 0:
                                                            if s_i_key in out_dict:
                                                                out_dict[s_i_key].append(t_out)
                                                            else:
                                                                out_dict[s_i_key] = [t_out]

                                # for ti_sets in t_i_dict[t_key]:
                                #     ti_set.append(ti_sets[1])
                                #
                                #         common = list(set(si_set).intersection(ti_set))
                                #         if len(common) > 1:
                                #             if s_i_key in out_dict:
                                #                 out_dict[s_i_key].append(t_key)
                                #             else:
                                #                 out_dict[s_i_key] = [t_key]
                                #             info_dict[t_key] = [t_rep, it_pos]
                                #             info_dict[s_i_key] = [s_rep, si_pos]
                                        #else:
                                        #    if s_i_key in non_ec_dict:
                                        #        non_ec_dict[s_i_key].append(t_key)
                                        #    else:
                                        #        non_ec_dict[s_i_key] = [t_key]
                                # except:
                                #     # Ekkert fannst - hvað gera bændur?
                                #     pass
                    except Exception as e:
                        pass
                        # print(e)

                if s_t not in dict_of_dicts.keys():
                    dict_of_dicts[s_t] = {}
                s_t_dict = dict_of_dicts[s_t].copy()

                #print(s_t)
                #if s_t in ('en_fr', 'fr_en', 'pt_en', 'en_pt'):
                #    print(s_t, 'length')
                #    print(len(dict_of_dicts[s_t].keys()))

                #print(len(info_dict.keys()))

                keyctr = 0
                #print(len(out_dict.keys()))
                for key in out_dict.keys():
                    pass
                    #print(key)
                    #print(out_dict[key])
                    #for t_key in out_dict[key]:
                    #    pass
                        #print(t_key)

                for key in out_dict.keys():
                    #print(key)
                    #print(info_dict[key])
                    #print(out_dict[key])

                    #keyctr += 1
                    #if keyctr % 1000 == 0:
                    #    print(s_t, keyctr, len(list(out_dict.keys())))
                    for t_key in out_dict[key]:
                        #print(t_key)
                        #print(info_dict[t_key])
                        if key in s_t_dict.keys():
                            otac_ctr += 1
                            s_t_dict[key].append([info_dict[key][0], t_key, info_dict[t_key][0], info_dict[key][1]])
                        else:
                            #temp_list = [info_dict[key][0], info_dict[t_key][0], t_key, info_dict[key][1]]
                            #dict_of_dicts[s_t][key].append(temp_list)
                            s_t_dict[key] = [[info_dict[key][0], t_key, info_dict[t_key][0], info_dict[key][1]]]
                            #print(temp_list)
                            #print(info_dict[key][0], info_dict[t_key][0])
                            #print(s_i_key)
                            #if s_t == 'en_fr':
                            #    print(dict_of_dicts[s_t])

                        #if s_t in ('en_fr', 'fr_en', 'pt_en', 'en_pt'):
                            #print('in dict')
                            #print(dict_of_dicts[s_t][key])

                        #s_t_dict[key] = list(s_t_dict[key] for s_t_dict[key], _ in itertools.groupby(s_t_dict[key]))
                            #print(e)
                        #pass
                        #print('villa')
                        #print(e)
                        #Ekkert fannst - hvað gera bændur?
                dict_of_dicts[s_t] = s_t_dict.copy()
                #print(s_t)
                #if s_t in ('en_fr', 'fr_en', 'pt_en', 'en_pt'):
                #    print(s_t, 'length')
                #    print(len(dict_of_dicts[s_t].keys()))

            return
        except:
            return


def add_selected_syn():
    while True:
        try:
            p = q.get()
            temp_dict = {}
            total_dict = {}
            syn_dict = {}
            src_w = p[0]
            trg_w = p[1]
            o_pairs = other_pairs.copy()
            o_pairs.remove(p)
            s3 = src_w + '_' + trg_w
            t3 = trg_w + '_' + src_w
            temp_dict_s = {}
            for src in (src_w, trg_w):
                # for o in other_pairs:
                #     if o[0] == src:
                #         s1 = o[0] + '_' + o[1]
                #         temp_dict[s1] = dict_of_dicts[s1].copy()
                #         s2 = o[1] + '_' + o[0]
                #         temp_dict[s2] = dict_of_dicts[s2].copy()
                #     elif o[1] == src:
                #         s1 = o[1] + '_' + o[0]
                #         temp_dict[s1] = dict_of_dicts[s1].copy()
                #         s2 = o[0] + '_' + o[1]
                #         temp_dict[s2] = dict_of_dicts[s2].copy()
                pair_ctr = 0
                for o in o_pairs:
                    temp_pair_dict = {}
                    if o[0] == src:
                        pair_ctr += 1
                        s1 = o[0] + '_' + o[1]
                        s2 = o[1] + '_' + o[0]
                        curr = dict_of_dicts[s1].copy()
                        rev = dict_of_dicts[s2].copy()
                        for curr_key in curr.keys():
                            if curr_key not in temp_pair_dict.keys():
                                temp_pair_dict[curr_key] = {}
                            for translation in curr[curr_key]:
                                src_word, trg_key, trg_word, pos = translation
                                for backtrans in rev[trg_key]:
                                    backtrans_key = backtrans[1]
                                    if backtrans_key in temp_pair_dict[curr_key].keys():
                                        temp_pair_dict[curr_key][backtrans_key] += 1
                                    else:
                                        temp_pair_dict[curr_key] = {backtrans_key: 1}


                    elif o[1] == src:
                        pair_ctr += 1
                        s2 = o[0] + '_' + o[1]
                        s1 = o[1] + '_' + o[0]
                        curr = dict_of_dicts[s1].copy()
                        rev = dict_of_dicts[s2].copy()
                        for curr_key in curr.keys():
                            if curr_key not in temp_pair_dict.keys():
                                temp_pair_dict[curr_key] = {}
                            for translation in curr[curr_key]:
                                src_word, trg_key, trg_word, pos = translation
                                for backtrans in rev[trg_key]:
                                    backtrans_key = backtrans[1]
                                    if backtrans_key in temp_pair_dict[curr_key].keys():
                                        temp_pair_dict[curr_key][backtrans_key] += 1
                                    else:
                                        temp_pair_dict[curr_key] = {backtrans_key: 1}

                    for k in temp_pair_dict.keys():
                        for m in temp_pair_dict[k].keys():
                            if k in temp_dict_s.keys():
                                if m in temp_dict_s[k].keys():
                                    temp_dict_s[k][m]['sets'] += 1
                                    temp_dict_s[k][m]['total'] += temp_pair_dict[k][m]
                                else:
                                    temp_dict_s[k][m] = {'sets': 1, 'total': temp_pair_dict[k][m]}
                            else:
                                temp_dict_s[k] = {m: {'sets': 1, 'total': temp_pair_dict[k][m]}}

                #print(pair_ctr)
                for l in temp_dict_s.keys():
                    for t in temp_dict_s[l].keys():
                        if pair_ctr > 0:
                            ratio = float(temp_dict_s[l][t]['sets'] / pair_ctr)
                        else:
                            ratio = 0
                        if ratio > syn_ratio_threshold:
                            if (l != t):
                                #print(l, t, str(ratio))
                                if l in synonyms:
                                    synonyms[l][t] = ratio
                                else:
                                    synonyms[l] = {t: ratio}
            q.task_done()
        except Queue.Empty:
            return


def add_syn():
    while True:
        try:
            p = q.get()
            syn_dict = {}
            src = p[0]
            trg = p[1]
            o_pairs = other_pairs.copy()
            o_pairs.remove(p)
            s3 = src + '_' + trg
            t3 = trg + '_' + src
            for o in o_pairs:
                src_flag = True
                trg_flag = True
                if o[0] == src:
                    s1 = o[0] + '_' + o[1]
                    s2 = o[1] + '_' + o[0]
                elif o[1] == src:
                    s1 = o[1] + '_' + o[0]
                    s2 = o[0] + '_' + o[1]
                else:
                    src_flag = False

                if o[0] == trg:
                    t1 = o[0] + '_' + o[1]
                    t2 = o[1] + '_' + o[0]
                elif o[1] == trg:
                    t1 = o[1] + '_' + o[0]
                    t2 = o[0] + '_' + o[1]
                else:
                    trg_flag = False

                if src_flag:
                    if s3 in syn_dict.keys():
                        syn_dict[s3].append([s1, s2, s3])
                    else:
                        syn_dict[s3] = [[s1, s2, s3]]

                if trg_flag:
                    if t3 in syn_dict.keys():
                        syn_dict[t3].append([t1, t2, t3])
                    else:
                        syn_dict[t3] = [[t1, t2, t3]]
                pivot_path(syn_dict)
                syn_dict = {}
            q.task_done()
        except Queue.Empty:
            return


def write_checkpoint():
    while True:
        try:
            curr_dict, addsynonym, location = q.get()
            out_list = []
            for key in curr_dict.keys():
                translations = curr_dict[key]
                for i in translations:
                    word = key.split('__')[1]
                    out_list.append(word + '\t' + i[2] + '\t' + key.split('__')[0] + '\t' + i[1].split('__')[0] + '\t' + i[3] + '\n')

            out_list = list(set(out_list))
            out_list.sort()

            pathway_out = pathway
            if addsynonym == 1:
                pathway_out = pathway + '_syn3'
            elif addsynonym == 2:
                pathway_out = pathway + '_syn_syn3'
            elif addsynonym == 3:
                pathway_out = pathway + '_syn_syn_syn3'

            with open(transset_folder + 'apertium/checkpoints/checkpoint' + '_' + location + '_' + pathway_out + '_' + src_lang + '_' + trg_lang + '.txt_new', 'w') as fo:
                for i in out_list:
                    fo.write(i)
            q.task_done()
        except Queue.Empty:
            return


if __name__ == '__main__':
    pairs = [['an', 'ca'], ['br', 'fr'], ['ca', 'it'], ['ca', 'sc'], ['cy', 'en'], ['en', 'ca'], ['en', 'es'], ['en', 'gl'],
             ['en', 'kk'], ['eo', 'ca'], ['eo', 'en'], ['eo', 'es'], ['eo', 'fr'], ['es', 'an'], ['es', 'ast'], ['es', 'ca'],
             ['es', 'gl'], ['es', 'it'], ['es', 'pt'], ['es', 'ro'], ['eu', 'en'], ['eu', 'es'], ['fr', 'ca'], ['fr', 'es'],
             ['is', 'en'], ['mk', 'en'], ['oc', 'ca'], ['oc', 'es'], ['oc', 'fr'], ['pt', 'ca'], ['pt', 'gl'], ['ro', 'ca'],
             ['sh', 'en']]



    jobs = []
    print('Reading files...')

    for i in pairs:
        p = multiprocessing.Process(name=i, target=work_pair, args=(i, dict_of_dicts))
        jobs.append(p)
        p.start()
    for j in jobs:
        j.join()
    print('ALL JOINED!!!')

    syn_count = 0
    print('Doing synonym stuff...')
    while syn_count < addsynonym:
        print('add synonyms - iteration ', str(syn_count+1))
        q = Queue()
        num_threads = 20
        other_pairs = pairs.copy()
        for i in range(num_threads):
            worker = Thread(target=add_selected_syn)
            worker.daemon = False
            worker.start()
        for p in pairs:
            q.put((p))
        q.join()
        syn_count += 1

    print(len(synonyms.keys()))

    if addsynonym > 0:
        print('Synonym stuff done!')

    extra_pairs = [['en', 'fr'], ['en', 'pt'], ['pt', 'fr'], ['fr', 'en'], ['pt', 'en'], ['fr', 'pt']]
    #for i in extra_pairs:
    #    pairs.append(i)

    print(dict_of_dicts.keys())
    jobs = []
    print('OTAC...')

    # for i in extra_pairs:
    #     #att_otac(i, dict_of_dicts)
    # # for i in extra_pairs:
    #     p = multiprocessing.Process(name=i, target=att_otac, args=(i, dict_of_dicts))
    #     jobs.append(p)
    #     p.start()
    #     #rev_pair = [i[1], i[0]]
    #     #p = multiprocessing.Process(name=rev_pair, target=att_otac, args=(rev_pair, dict_of_dicts))
    #     #jobs.append(p)
    #     #p.start()
    # for j in jobs:
    #     j.join()
    # print(dict_of_dicts.keys())
    # print(len(dict_of_dicts['fr_en'].keys()))

    if pathway == 'max2edges':
        path_dict = {
        'en_fr': (('en_eo', 'eo_fr'), ('en_es', 'es_fr'), ('en_ca', 'ca_fr')),
        'fr_en': (('fr_eo', 'eo_en'), ('fr_es', 'es_en'), ('fr_ca', 'ca_en')),
        'fr_pt': (('fr_ca', 'ca_pt'), ('fr_es', 'es_pt')),
        'pt_fr': (('pt_ca', 'ca_fr'), ('pt_es', 'es_fr')),
        'en_pt': (('en_ca', 'ca_pt'), ('en_gl', 'gl_pt'), ('en_es', 'es_pt')),
        'pt_en': (('pt_ca', 'ca_en'), ('pt_gl', 'gl_en'), ('pt_es', 'es_en'))
        }
    elif pathway == 'max3edges':
        path_dict = {
        'en_fr': (('en_eo', 'eo_fr'), ('en_es', 'es_fr'), ('en_ca', 'ca_fr'), ('en_eu', 'eu_es', 'es_fr'), ('en_gl', 'gl_es', 'es_fr'), ('en_ca', 'ca_es', 'es_fr'), ('en_ca', 'ca_oc', 'oc_fr'), ('en_ca', 'ca_eo', 'eo_fr'), ('en_eo', 'eo_es', 'es_fr'), ('en_eo', 'eo_ca', 'ca_fr'), ('en_es', 'es_oc', 'oc_fr'), ('en_es', 'es_ca', 'ca_fr'), ('en_es', 'es_eo', 'eo_fr')),
        'fr_en': (('fr_eo', 'eo_en'), ('fr_es', 'es_en'), ('fr_ca', 'ca_en'), ('fr_es', 'es_eu', 'eu_en'), ('fr_es', 'es_gl', 'gl_en'), ('fr_es', 'es_ca', 'ca_en'), ('fr_oc', 'oc_ca', 'ca_en'), ('fr_eo', 'eo_ca', 'ca_en'), ('fr_es', 'es_eo', 'eo_en'), ('fr_ca', 'ca_eo', 'eo_en'), ('fr_oc', 'oc_es', 'es_en'), ('fr_ca', 'ca_es', 'es_en'), ('fr_eo', 'eo_es', 'es_en')),
        'fr_pt': (('fr_ca', 'ca_pt'), ('fr_es', 'es_pt'), ('fr_es', 'es_gl', 'gl_pt'), ('fr_es', 'es_ca', 'ca_pt'), ('fr_eo', 'eo_ca', 'ca_pt'), ('fr_oc', 'oc_ca', 'ca_pt'), ('fr_oc', 'oc_es', 'es_pt'), ('fr_eo', 'eo_es', 'es_pt'), ('fr_ca', 'ca_es', 'es_pt')),
        'pt_fr': (('pt_ca', 'ca_fr'), ('pt_es', 'es_fr'), ('pt_gl', 'gl_es', 'es_fr'), ('pt_ca', 'ca_es', 'es_fr'), ('pt_ca', 'ca_eo', 'eo_fr'), ('pt_ca', 'ca_oc', 'oc_fr'), ('pt_es', 'es_oc', 'oc_fr'), ('pt_es', 'es_eo', 'eo_fr'), ('pt_es', 'es_ca', 'ca_fr')),
        'en_pt': (('en_ca', 'ca_pt'), ('en_gl', 'gl_pt'), ('en_es', 'es_pt'), ('en_es', 'es_gl', 'gl_pt'), ('en_eo', 'eo_es', 'es_pt'), ('en_ca', 'ca_es', 'es_pt'), ('en_eu', 'eu_es', 'es_pt'), ('en_gl', 'gl_es', 'es_pt'), ('en_eo', 'eo_ca', 'ca_pt'), ('en_es', 'es_ca', 'ca_pt')),
        'pt_en': (('pt_ca', 'ca_en'), ('pt_gl', 'gl_en'), ('pt_es', 'es_en'), ('pt_gl', 'gl_es', 'es_en'), ('pt_es', 'es_eo', 'eo_en'), ('pt_es', 'es_ca', 'ca_en'), ('pt_es', 'es_eu', 'eu_en'), ('pt_es', 'es_gl', 'gl_en'), ('pt_ca', 'ca_eo', 'eo_en'), ('pt_ca', 'ca_es', 'es_en'))
        }

    pivot_ctr = 0
    while pivot_ctr < 1:
        pivot_ctr += 1
        print('pivot dicts')
        q = Queue()
        num_threads = 20
        for i in range(num_threads):
            worker = Thread(target=pivot_path_dict)
            worker.daemon = False
            worker.start()
        for j in path_dict.keys():
            q.put((j, path_dict))
        q.join()

    #
    # final_pairs = [['en', 'fr'], ['fr', 'pt'], ['en', 'pt']]
    # jobs = []
    # print('OTAC...')
    #
    # for i in final_pairs:
    #     p = multiprocessing.Process(name=i, target=att_otac, args=(i, dict_of_dicts))
    #     jobs.append(p)
    #     p.start()
    #     rev_pair = [i[1], i[0]]
    #     p = multiprocessing.Process(name=rev_pair, target=att_otac, args=(rev_pair, dict_of_dicts))
    #     jobs.append(p)
    #     p.start()
    # for j in jobs:
    #     j.join()


    #pivot_path(path_dict)
    #print(dict_of_dicts['en_fr'])

    #print('Writing checkpoint "syn_"' + pathway + '...')
    #for i in dict_of_dicts.keys():
    #    write_checkpoint(dict_of_dicts[i], addsynonym, "syn_" + pathway)

    #vantar að lúppa í gegnum tilbúnu þýðingarnar áður en lokaþýðingar eru búnar til
    # pivots_path_dict = {
    #     'en_fr': [('en_fr', 'fr_en', 'en_fr'), ('en_pt', 'pt_en', 'en_fr')],
    #     'fr_en': [('fr_pt', 'pt_fr', 'fr_en'), ('fr_pt', 'pt_fr', 'fr_en')],
    #     'fr_pt': [('fr_en', 'en_fr', 'fr_pt'), ('fr_en', 'en_fr', 'fr_en')],
    #     'pt_fr': [('pt_en', 'en_pt', 'pt_fr'), ('pt_en', 'en_pt', 'pt_fr')],
    #     'en_pt': [('en_fr', 'fr_en', 'en_pt'), ('en_fr', 'fr_en', 'en_fr')],
    #     'pt_en': [('pt_fr', 'fr_pt', 'pt_fr'), ('pt_fr', 'fr_pt', 'pt_en')]
    # }
    #
    # print('Pivot path dicts...')
    # q = Queue()
    # num_threads = 20
    # for i in range(num_threads):
    #     worker = Thread(target=pivot_path_dict)
    #     worker.daemon = False
    #     worker.start()
    # for j in pivots_path_dict.keys():
    #     q.put((j, pivots_path_dict))
    # #pivot_path(pivots_path_dict)
    # q.join()

    # print('Writing checkpoint "syn_"' + pathway + '_finaldicts' + '...')
    # q = Queue()
    # num_threads = 12
    # for i in range(num_threads):
    #     worker = Thread(target=write_checkpoint, args=(q,))
    #     worker.daemon = False
    #     worker.start()
    # for i in dict_of_dicts.keys():
    #     q.put((dict_of_dicts[i], addsynonym, "syn_" + pathway + '_finaldicts'))
    #     #write_checkpoint(dict_of_dicts[i], addsynonym, "syn_" + pathway + '_finaldicts')
    # q.join()


    pivots_path_dict = {
        'en_fr': [('en_pt', 'pt_fr')],
        'fr_en': [('fr_pt', 'pt_en')],
        'fr_pt': [('fr_en', 'en_pt')],
        'pt_fr': [('pt_en', 'en_fr')],
        'en_pt': [('en_fr', 'fr_pt')],
        'pt_en': [('pt_fr', 'fr_en')]
    }
    print('Pivot pivot path dicts...')
    pivot_ctr = 1
    while pivot_ctr < 1:
        pivot_ctr += 1
        q = Queue()
        num_threads = 8
        for i in range(num_threads):
            worker = Thread(target=pivot_path_dict)
            worker.daemon = False
            worker.start()
        for j in pivots_path_dict.keys():
            q.put((j, pivots_path_dict))
        #pivot_path(pivots_path_dict)
        q.join()

    #while syn_count < addsynonym:
    while 1 == 2:
        print('add synonyms - iteration ', str(syn_count+1))
        q = Queue()
        num_threads = 20
        other_pairs = pairs.copy()
        for i in range(num_threads):
            worker = Thread(target=add_selected_syn)
            worker.daemon = False
            worker.start()
        for pair in pivots_path_dict.keys():
            p = pair.split('_')
            q.put((p))
        q.join()
        syn_count += 1

    print('ALL DONE! Writing to files...')
    #print(dict_of_dicts['en_fr'])

    for pivots in pivots_path_dict.keys():
        src_lang, trg_lang = pivots.split('_')
        curr_dict = dict_of_dicts[pivots]

        out_list = []

        for key in curr_dict.keys():
            translations = curr_dict[key]
            for i in translations:
                word = key.split('__')[1]
                out_list.append(word + '\t' + i[2] + '\t' + key.split('__')[0] + '\t' + i[1].split('__')[0] + '\t' + i[3] + '\n')

        out_list = list(set(out_list))
        out_list.sort()

        pathway_out = pathway + '_ttac_paths' + str(addsynonym)

        with open(transset_folder + 'apertium/' + 'test_' + pathway_out + '_' + src_lang + '_' + trg_lang + '.txt', 'w') as fo:
            for i in out_list:
                fo.write(i)

        with open(transset_folder + 'apertium/' + 'before_filter_' + pathway_out + '_' + src_lang + '_' + trg_lang + '.txt', 'w') as fo:
            for i in out_list:
                temp = i.strip().split('\t')
                pos = temp[4].strip('"').split('#')
                try:
                    fo.write(temp[0] + '\t' + temp[1] + '\t' + temp[4].strip('"').split('#')[1] + '\n')
                except:
                    print(temp)
                    sys.exit(0)

        #Sækja lista af öllum orðum í ákveðnu tungumáli í skránum - sækja lista yfir það sem ekki hefur fundist
        en_words = []
        en_words_found = []

        for i in out_list:
            en_words_found.append(i.split('\t')[2].strip())

        en_words_found = list(set(en_words_found))
        with open(transset_folder + 'apertium/' + pathway_out + '_' + src_lang + '_' + trg_lang + '_words.txt', 'w') as fo:
            for i in en_words_found:
                fo.write(i + '\n')

        pairs_found = []
        for i in out_list:
            pairs_found.append(i.split('\t')[0].strip() + '\t' + i.split('\t')[1].strip())

        pairs_found = list(set(pairs_found))
        pairs_found.sort()
        with open(transset_folder + 'apertium/' + pathway_out + '_' + src_lang + '_' + trg_lang + '_pairs3.txt', 'w') as fo:
            for i in pairs_found:
                fo.write(i + '\n')

    for key in dict_of_lists.keys():
        with open(transset_folder + 'apertium/' + key + '_' + '_words.txt', 'w') as fo:
            output_list = dict_of_lists[key]
            output_list = list(set(output_list))
            output_list.sort()
            for i in output_list:
                fo.write(i + '\n')

