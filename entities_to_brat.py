#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import re
import os
import logging
import argparse
import unidecode

from collections import defaultdict


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Prepare Brat ANN files with entities detected by BTred.'
parser.add_argument('--dictionary', required=True, help='entities dictionary XML file')
parser.add_argument('--btred_dir', required=True, help='output file from BTred entity detection')
parser.add_argument('--pml_dir', required=True, help='directory with the PML CLTT files')
parser.add_argument('--brat_dir', required=True, help='directory where final TXT & ANN files will be created')
args = parser.parse_args()


# Methods.
def load_dictionary(file_path):
    dictionary = dict()
    entity_types = defaultdict(int)

    entity_id = None
    entity_type = None

    with open(file_path, 'r') as document:
        for line in document:
            line = line.decode('utf8')

            # Entity ID.
            entity_id_match = re.match(r'.*<entity id="(?P<entity_id>\d+)">', line)
            if entity_id_match:
                entity_id = entity_id_match.group('entity_id')

            # Entity Type.
            entity_type_match = re.match(r'.*<type>(?P<entity_type>.*)</type>', line)
            if entity_type_match:
                entity_type = entity_type_match.group('entity_type')

            if entity_id and entity_type:
                entity_type = unidecode.unidecode(entity_type)
                entity_type = re.sub(r' ', '_', entity_type)

                dictionary[entity_id] = entity_type
                entity_types[entity_type] += 1
                entity_id = None
                entity_type = None

    logging.info('Number of loaded entities: %d', len(dictionary))
    return dictionary, entity_types


def load_btred(btred_dir):
    """Load detected entites from the btred."""
    detected_entities = []

    btred_files = sorted(os.listdir(btred_dir))
    for n_file, file_name in enumerate(btred_files):
        file_name_match = re.match(r'(?P<document_id>document_0[12]_00\d).a-(?P<entity_id>\d+).txt', file_name)
        if not file_name_match:
            logging.warning('Could not parse %s filename.', file_name)
            continue

        document_id = file_name_match.group('document_id')
        entity_id = file_name_match.group('entity_id')

        full_path = '/'.join([btred_dir, file_name])
        with open(full_path, 'r') as bred_output:
            for line in bred_output:
                line = line.rstrip()

                node_ids = []
                for node_id in line.split('\t'):
                    node_id = re.sub(r'^a-', '', node_id)
                    node_ids.append(node_id)

                if node_ids:
                    detected_entities.append({
                        'document_id': document_id,
                        'entity_id': entity_id,
                        'nodes': node_ids,
                        'start_node': node_ids[0],
                        'end_node': node_ids[-1]
                    })

    logging.info('Loaded %d entities from %d files.', len(detected_entities), len(btred_files))
    return detected_entities


def load_pml(pml_dir):
    documents = []
    tokens_offsets = {}
    pml_files = sorted(os.listdir(pml_dir))

    for pml_file in pml_files:
        file_name_match = re.match(r'(?P<document_id>document_0[12]_00\d).m$', pml_file)
        if not file_name_match:
            continue

        char_offset = 0
        document_id = file_name_match.group('document_id')
        sentences = []

        full_path = '/'.join([pml_dir, pml_file])
        with open(full_path, 'r') as pml_data:
            tokens = []
            node_id = None
            node_form = None

            for line in pml_data:
                line = line.decode('utf-8')

                sentence_match = re.match(r'^\s+<s .*', line)
                if sentence_match:
                    if tokens:
                        logging.debug('Sentence end. Number of nodes: %d. Offset: %d', len(tokens), char_offset)
                        logging.debug('')
                        char_offset += 1
                        sentences.append(list(tokens))
                    tokens = []

                node_id_match = re.match(r'^\s+<m id="m-(?P<node_id>.*)">', line)
                if node_id_match:
                    node_id = node_id_match.group('node_id')

                node_form_match = re.match(r'^\s+<form>(?P<node_form>.*)</form>', line)
                if node_form_match:
                    node_form = node_form_match.group('node_form')

                if node_id and node_form:
                    start_offset = char_offset if not tokens else char_offset + 1
                    end_offset = start_offset + len(node_form)
                    char_offset = end_offset
                    tokens.append({'node_id': node_id, 'node_form': node_form, 'start_offset': start_offset, 'end_offset': end_offset})
                    tokens_offsets[node_id] = {'form': node_form, 'start': start_offset, 'end': end_offset}
                    logging.debug('%20s | %10d | %10d', node_form, start_offset, end_offset)
                    node_id = None
                    node_form = None

            if tokens:
                sentences.append(tokens)

        logging.info('Loaded %d sentences from document %s', len(sentences), document_id)
        documents.append({'document_id': document_id, 'sentences': sentences})

    return documents, tokens_offsets


def create_plaintext_files(documents, brat_dir):
    for document in documents:
        document_id = document['document_id']
        full_path = '/'.join([brat_dir, document_id + '.txt'])
        with open(full_path, 'w') as output_file:
            for sentence in document['sentences']:
                line = ' '.join(token['node_form'] for token in sentence)
                output_file.write(line.encode('utf8'))
                output_file.write('\n')


def create_annotation_files(documents, node_offsets, entities, dictionary, brat_dir):
    for document in documents:
        document_id = document['document_id']
        full_path = '/'.join([brat_dir, document_id + '.ann'])
        with open(full_path, 'w') as output_file:
            entity_counter = 0
            sorted_entities = sorted(entities, key=lambda entity:node_offsets[entity['start_node']]['start'])
            for entity in sorted_entities:
                if entity['document_id'] != document_id:
                    continue

                entity_counter += 1
                entity_ord = 'T%d' % entity_counter
                entity_type = dictionary[entity['entity_id']]
                start_offest = node_offsets[entity['start_node']]['start']
                end_offset = node_offsets[entity['end_node']]['end']
                entity_form = ' '.join([node_offsets[node]['form'] for node in entity['nodes']])
                chunk_triple = '%s %d %d' % (entity_type, start_offest, end_offset)
                line = '\t'.join([entity_ord, chunk_triple, entity_form])
                output_file.write(line.encode('utf8'))
                output_file.write('\n')


def filter_out_subentities(entities):
    """
    Filter out entities that are included in more specific ones.

    """
    filtered_entities = []
    for candidate_entity in sorted(entities, key=lambda entity:len(entity['nodes']), reverse=True):
        candidate_entity_nodes = set(candidate_entity['nodes'])

        exists_more_specific_entity = False
        for filtered_entity in filtered_entities:
            filtered_entities_nodes = set(filtered_entity['nodes'])
            if candidate_entity_nodes.issubset(filtered_entities_nodes):
                exists_more_specific_entity = True
                break

        if not exists_more_specific_entity:
            filtered_entities.append(candidate_entity)

    logging.info('Number of entities after subentities filtering: %d', len(filtered_entities))
    return filtered_entities


def filter_out_noncontinous_entities(entities):
    filtered_entities = []
    for candidate_entity in entities:
        continuous_entity = True

        previous_ord = None
        for node in candidate_entity['nodes']:
            current_ord = int(re.sub(r'^.*node(\d+)$', r'\1', node))
            if previous_ord and current_ord != previous_ord + 1:
                continuous_entity = False
                break
            else:
                previous_ord = current_ord

        if continuous_entity:
            filtered_entities.append(candidate_entity)

    logging.info('Number of entities after continuous control: %d', len(filtered_entities))
    return filtered_entities



# Main.
if __name__ == "__main__":
    dictionary, entity_types = load_dictionary(args.dictionary)
    entities = load_btred(args.btred_dir)
    entities = filter_out_subentities(entities)
    entities = filter_out_noncontinous_entities(entities)
    documents, node_offsets = load_pml(args.pml_dir)
    create_plaintext_files(documents, args.brat_dir)
    create_annotation_files(documents, node_offsets, entities, dictionary, args.brat_dir)
