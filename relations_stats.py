#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import os
import logging
import argparse
import json
import re

from collections import defaultdict

from cltt.accounting_dictionary import Dictionary

# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Prepare a plaintext report with different statistics about the CLTT R-LAYER.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--relations', required=True, help='JSON R-layer file dir.')
args = parser.parse_args()

# Load dictionary.
dictionary = Dictionary()
dictionary.load_json(args.dictionary)

# Translate dictionary categories to English
cz_category2en_category = {
    'aktivum': 'assets',
    'cinnost': 'activity',
    'dan': 'taxes',
    'fyzicka_osoba': 'natural person',
    'instituce': 'institution',
    'metoda': 'method',
    'naklad': 'costs',
    'obdobi': 'period',
    'obecny_dokument': 'document',
    'obecny_pojem': 'general term',
    'obecny_subjekt': 'general subject',
    'okamzik': 'moment',
    'pasivum': 'liabilities',
    'povinnost': 'obligation',
    'pravnicka_osoba': 'legal person',
    'organ_pravnicke_osoby': 'legal person',
    'pravo': 'right',
    'predpis': 'regulation',
    'prijem': 'incomes',
    'smlouva': 'agreement',
    'stav': 'state',
    'ucet': 'account',
    'ucetni_pojem': 'accounting concept',
    'obecny_ucetni_pojem': 'accounting concept',
    'ucetni_vykaz': 'accounting report',
    'vydaj': 'expenses',
    'vynos': 'revenues'
}


# Initialize counters.
n_total = 0
n_sentences = 1121
relation_types = defaultdict(int)
number_of_relations_in_sentence = defaultdict(int)
top_subject_entities = defaultdict(int)
top_subject_categories = defaultdict(int)
top_object_entities = defaultdict(int)
top_object_categories = defaultdict(int)
top_predicates = defaultdict(lambda: defaultdict(int))

# Process CLTT relations.
document_ids = [document[:-5] for document in sorted(os.listdir(args.relations)) if document[-5:] == '.json']
for document_id in document_ids:
    logging.info('Processing document %s.', document_id)

    file_name = '/'.join([args.relations, document_id + '.json'])
    relations = json.load(open(file_name, 'r'))

    for relation in relations:
        n_total += 1
        relation_type = relation['relation_type']
        sentence_id = re.sub('(document_\d+_\d+-sentence\d+)-.*', '\\1', relation['subject']['node_ids'][0])
        subject_dictionary_id = relation['subject']['dictionary_id']
        subject_dictionary_category = cz_category2en_category[relation['subject']['entity_type']]
        object_dictionary_id = relation['object']['dictionary_id']
        object_dictionary_category = cz_category2en_category[relation['object']['entity_type']]
        predicate = relation['predicate']['text_chunk_form']

        relation_types[relation_type] += 1
        number_of_relations_in_sentence[sentence_id] += 1
        top_subject_entities[subject_dictionary_id] += 1
        top_subject_categories[subject_dictionary_category] += 1
        top_object_entities[object_dictionary_id] += 1
        top_object_categories[object_dictionary_category] += 1
        top_predicates[relation_type][predicate] += 1

# Postprocess data
sentence_relations_distribution = defaultdict(int)
sentence_relations_distribution[0] = n_sentences - len(number_of_relations_in_sentence)
for sentence_id, number_of_relations in number_of_relations_in_sentence.iteritems():
    sentence_relations_distribution[number_of_relations] += 1

print ''
print '# of relations = %d' % n_total


print ''
print '*******************************************'
print '* Relation type distribution'
print ''
print 'Type;Frequency'
for relation_type, frequency in relation_types.items():
    print '{};{};{:.2%}'.format(relation_type, frequency, frequency / float(n_total))

print ''
print '*******************************************'
print '* Number of relations in one sentence'
print ''
print 'Number of relations in one sentence;Frequency'
for number_of_relations, frequency in sentence_relations_distribution.items():
    print '{};{};{:.2%}'.format(number_of_relations, frequency, frequency / float(n_sentences))

print ''
print '*******************************************'
print '* Top subject entities'
print ''
print 'Subject;Frequency'
for subject_entity_id in sorted(top_subject_entities.keys(), key=lambda subject:top_subject_entities[subject], reverse=True)[:10]:
    print '{};{};{:.2%}'.format(dictionary.dictionary[subject_entity_id]['entity_form'].encode('utf-8'), top_subject_entities[subject_entity_id], top_subject_entities[subject_entity_id] / float(n_total))

print ''
print '*******************************************'
print '* Top subject categories'
print ''
print 'Category;Frequency'
for subject_category in sorted(top_subject_categories.keys(), key=lambda subject:top_subject_categories[subject], reverse=True)[:10]:
    print '{};{};{:.2%}'.format(subject_category, top_subject_categories[subject_category], top_subject_categories[subject_category] / float(n_total))

print ''
print '*******************************************'
print '* Top object entities'
print ''
print 'object;Frequency'
for object_entity_id in sorted(top_object_entities.keys(), key=lambda objectt:top_object_entities[objectt], reverse=True)[:10]:
    print '{};{};{:.2%}'.format(dictionary.dictionary[object_entity_id]['entity_form'].encode('utf-8'), top_object_entities[object_entity_id], top_object_entities[object_entity_id] / float(n_total))

print ''
print '*******************************************'
print '* Top object categories'
print ''
print 'Category;Frequency'
for object_category in sorted(top_object_categories.keys(), key=lambda objectt:top_object_categories[objectt], reverse=True)[:10]:
    print '{};{};{:.2%}'.format(object_category, top_object_categories[object_category], top_object_categories[object_category] / float(n_total))

for relation_type, frequency in relation_types.items():
    print ''
    print '*******************************************'
    print '* Top %s predicates' % relation_type
    print ''
    print 'Predicate;Frequency'
    for predicate in sorted(top_predicates[relation_type].keys(), key=lambda predicate:top_predicates[relation_type][predicate], reverse=True)[:10]:
        print '{};{};{:.2%}'.format(predicate.encode('utf-8'), top_predicates[relation_type][predicate], top_predicates[relation_type][predicate] / float(frequency))

