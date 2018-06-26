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
parser.description = 'Add data about detected entities into PML m-files.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--entities', required=True, help='Json files with the annotation.')
args = parser.parse_args()

# Load dictionary.
dictionary = Dictionary()
dictionary.load_json(args.dictionary)

# Initialize counters.
n_total = 0
unique_entities = {}
sentence_entities = defaultdict(int)
category_entities_abs = defaultdict(int)
category_entities_unique_dict = defaultdict(int)

for dictionary_id in dictionary.dictionary:
    entry = dictionary.dictionary[dictionary_id]
    entity_type = entry['entity_type']
    if entity_type == 'organ_pravnicke_osoby':
        entity_type = 'pravnicka_osoba'
    if entity_type == 'obecny_ucetni_pojem':
        entity_type = 'ucetni_pojem'
    category_entities_unique_dict[entity_type] += 1

# Process CLTT entities.
document_ids = [document[:-5] for document in sorted(os.listdir(args.entities)) if document[-5:] == '.json']
for document_id in document_ids:
    logging.info('Processing document %s.', document_id)

    file_name = '/'.join([args.entities, document_id + '.json'])
    entities = json.load(open(file_name, 'r'))

    n_total += len(entities)
    for entity in entities:
        dictionary_id = entity['dictionary_id']
        sentence_id = re.sub(r'^(.*sentence\d+).*', '\\1', entity['node_ids'][0])
        entity_type = entity['entity_type']
        if entity_type == 'organ_pravnicke_osoby':
            entity_type = 'pravnicka_osoba'
        if entity_type == 'obecny_ucetni_pojem':
            entity_type = 'ucetni_pojem'
        # logging.info('Node: %s --> Sentence: %s', entity['node_ids'][0], sentence_id)
        unique_entities[dictionary_id] = 1
        sentence_entities[sentence_id] += 1
        category_entities_abs[entity_type] += 1

entities_per_sentence = defaultdict(int)
entities_per_sentence['0'] = 1121 - len(sentence_entities)
for sentence_id, n_entities in sentence_entities.iteritems():
    if n_entities < 20:
        entities_per_sentence[n_entities] += 1
    elif 20 <= n_entities < 30:
        entities_per_sentence['20-30'] += 1
    elif 30 <= n_entities < 40:
        entities_per_sentence['30-40'] += 1
    elif 40 <= n_entities < 50:
        entities_per_sentence['40-50'] += 1
    elif 50 <= n_entities < 60:
        entities_per_sentence['50-60'] += 1
    elif 60 <= n_entities < 70:
        entities_per_sentence['60-70'] += 1
    elif 70 <= n_entities < 80:
        entities_per_sentence['70-80'] += 1
    elif 80 <= n_entities < 90:
        entities_per_sentence['80-90'] += 1
    elif 90 <= n_entities < 100:
        entities_per_sentence['90-100'] += 1
    elif 100 <= n_entities < 110:
        entities_per_sentence['100-110'] += 1
    elif 110 <= n_entities < 120:
        entities_per_sentence['110-120'] += 1
    elif 120 <= n_entities < 130:
        entities_per_sentence['120-130'] += 1
    elif 130 <= n_entities < 140:
        entities_per_sentence['130-140'] += 1
    elif 140 <= n_entities < 150:
        entities_per_sentence['140-150'] += 1
    elif 150 <= n_entities < 160:
        entities_per_sentence['150-160'] += 1
    elif 160 <= n_entities < 170:
        entities_per_sentence['160-170'] += 1
    elif 170 <= n_entities < 180:
        entities_per_sentence['170-180'] += 1
    elif 180 <= n_entities < 190:
        entities_per_sentence['180-190'] += 1
    elif 190 <= n_entities < 200:
        entities_per_sentence['190-200'] += 1
    else:
        entities_per_sentence['200+'] += 1

# Report statistics.
logging.info('')
logging.info('-----')
logging.info('# of entities           : %d', n_total)
logging.info('# of dictionary entries : %d', len(dictionary.dictionary))
logging.info('# of unique entities    : %d', len(unique_entities))

logging.info('')
logging.info('-----')
logging.info('%20s | %2s', '# of entities', '# of sentences')
for n_entities, n_sentences in entities_per_sentence.iteritems():
    logging.info('%20s | %20d', n_entities, n_sentences)

logging.info('')
logging.info('-----')
logging.info('%20s | %2s', 'category', '# of entities')
for category, n_entities in category_entities_abs.iteritems():
    logging.info('%20s | %20d', category, n_entities)


logging.info('')
logging.info('-----')
logging.info('%20s | %2s', 'category', '# of unique entities')
for category, n_entities in category_entities_unique_dict.iteritems():
    logging.info('%20s | %20d', category, n_entities)


# for dictionary_id in dictionary.dictionary:
#     if dictionary_id not in unique_entities:
#         logging.warning('Unused entry: %r', dictionary.dictionary[dictionary_id])