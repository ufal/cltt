#!/usr/bin/env python
#
# Author: (c) 2018 Vincent Kriz <kriz@ufal.mff.cuni.cz>

"""
Adaptation of the entities_processing for the multiplicated sentences.

"""

import os
import logging
import argparse
import json
import re

from cltt.accounting_dictionary import Dictionary
from cltt.pml import load_m_file, put_entities_into_m_files


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Add data about detected entities into PML m-files.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--elayer', required=True, help='Original e-layer JSON files directory')
parser.add_argument('--cltt', required=True, help='Multiplicated sentences PML files directory')
parser.add_argument('--pml', required=True, default=None, help='New e-layer PML files')
parser.add_argument('--json', required=True, help='New e-layer JSON files')
args = parser.parse_args()


if __name__ == "__main__":
    # Accounting Dictionary.
    accounting_dictionary = Dictionary()
    accounting_dictionary.load_json(args.dictionary)
    accounting_entities, entity_types = accounting_dictionary.dictionary, accounting_dictionary.entity_types

    document_ids = [document[:-2] for document in sorted(os.listdir(args.cltt)) if document[-2:] == '.m']
    for document_id in document_ids:
        logging.info('Processing document %s :', document_id)

        # Load PML files with multiplicated sentences.
        cltt_m_filename = '{}/{}.m'.format(args.cltt, document_id)
        document = load_m_file(cltt_m_filename)
        document_nodes = set([token['node_id'] for sentence in document['sentences'] for token in sentence])

        # Load original e-layer JSON files.
        elayer_json_filename = '{}/{}.json'.format(args.elayer, document_id)
        original_entities = json.load(open(elayer_json_filename, 'r'))

        # Process each original entity.
        multiplicated_entities = []
        for original_entity in original_entities:
            logging.info('')
            logging.info('Processing entity %r', original_entity)

            if set(original_entity['node_ids']).issubset(document_nodes):
                multiplicated_entities.append(original_entity)
            else:
                sentence_id = re.sub('.*(sentence\d+).*', '\\1', original_entity['node_ids'][0])
                for sentence in [sentence for sentence in document['sentences'] if re.sub('.*(sentence\d+).*', '\\1', sentence[0]['node_id']) == sentence_id]:
                    multiplicated_nodes = [token['node_id'] for token in sentence]
                    multiplicated_entity_nodes = [node_id for node_id in multiplicated_nodes if re.sub('-multiplication\d+\.\d+', '', node_id) in original_entity['node_ids']]

                    if not multiplicated_entity_nodes:
                        continue

                    logging.info('')
                    logging.info(' -> Multiplicated sentence = %s', sentence[0]['node_id'])
                    logging.info(' -> Original nodes         = %r', original_entity['node_ids'])
                    logging.info(' -> Multiplicated nodes    = %r', multiplicated_entity_nodes)

                    multiplicated_entity = original_entity.copy()
                    multiplicated_entity['node_ids'] = multiplicated_entity_nodes
                    multiplicated_entity['text_chunk_start_offset'] = document['token_offsets'][multiplicated_entity_nodes[0]]['start']
                    multiplicated_entity['text_chunk_end_offset'] = document['token_offsets'][multiplicated_entity_nodes[-1]]['end']

                    multiplicated_entities.append(multiplicated_entity)

        # Encode forms into UTF-8.
        for multiplicated_entity in multiplicated_entities:
            multiplicated_entity['text_chunk_form'] = multiplicated_entity['text_chunk_form'].encode('utf8')

        # Create json-elayer file.
        json_filename = '{}/{}.json'.format(args.json, document_id)
        json.dump(multiplicated_entities, open(json_filename, 'w'), ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))

        # Create pml-elayer file.
        pml_m_filename = '{}/{}.m'.format(args.pml, document_id)
        put_entities_into_m_files(multiplicated_entities, accounting_dictionary, cltt_m_filename, pml_m_filename)
