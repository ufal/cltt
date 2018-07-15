#!/usr/bin/env python
#
# Author: (c) 2018 Vincent Kriz <kriz@ufal.mff.cuni.cz>

"""
Adaptation of the relations_processing for the multiplicated sentences.

"""

import os
import logging
import argparse
import json
import re

from cltt.accounting_dictionary import Dictionary
from cltt.pml import load_m_file, put_relations_into_m_files


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Add data about detected relations into PML m-files.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--rlayer', required=True, help='Original r-layer JSON files directory')
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

        # Load original r-layer JSON files.
        rlayer_json_filename = '{}/{}.json'.format(args.rlayer, document_id)
        original_relations = json.load(open(rlayer_json_filename, 'r'))

        # Process each original relation.
        multiplicated_relations = []
        for original_relation in original_relations:
            logging.info('')
            logging.info('Processing relation %s', original_relation['relation_id'])

            original_relation_nodes = [node_id for node_id in original_relation['subject']['node_ids']] + [node_id for node_id in original_relation['predicate']['node_ids']] + [node_id for node_id in original_relation['object']['node_ids']]
            logging.info(' -> original nodes = %r', original_relation_nodes)

            if set(original_relation_nodes).issubset(document_nodes):
                multiplicated_relations.append(original_relation)
                logging.info(' -> relation is the same also in multiplicated dataset.')
            else:
                sentence_id = re.sub('.*(sentence\d+).*', '\\1', original_relation_nodes[0])
                for sentence in [sentence for sentence in document['sentences'] if re.sub('.*(sentence\d+).*', '\\1', sentence[0]['node_id']) == sentence_id]:
                    multiplicated_nodes = [token['node_id'] for token in sentence]
                    multiplicated_subject_nodes = [node_id for node_id in multiplicated_nodes if re.sub('-multiplication\d+\.\d+', '', node_id) in original_relation['subject']['node_ids']]
                    multiplicated_predicate_nodes = [node_id for node_id in multiplicated_nodes if re.sub('-multiplication\d+\.\d+', '', node_id) in original_relation['predicate']['node_ids']]
                    multiplicated_object_nodes = [node_id for node_id in multiplicated_nodes if re.sub('-multiplication\d+\.\d+', '', node_id) in original_relation['object']['node_ids']]

                    if not (multiplicated_subject_nodes and multiplicated_predicate_nodes and multiplicated_object_nodes):
                        continue

                    logging.info('')
                    logging.info(' -> Multiplicated sentence = %s', sentence[0]['node_id'])
                    logging.info(' -> Original SUBJ nodes    = %r', original_relation['subject']['node_ids'])
                    logging.info(' -> Multipli SUBJ nodes    = %r', multiplicated_subject_nodes)
                    logging.info(' -> Original PRED nodes    = %r', original_relation['predicate']['node_ids'])
                    logging.info(' -> Multipli PRED nodes    = %r', multiplicated_predicate_nodes)
                    logging.info(' -> Original OBJ  nodes    = %r', original_relation['object']['node_ids'])
                    logging.info(' -> Multipli OBJ  nodes    = %r', multiplicated_object_nodes)

                    multiplicated_relation = original_relation.copy()
                    multiplicated_relation['subject']['node_ids'] = multiplicated_subject_nodes
                    multiplicated_relation['subject']['text_chunk_start_offset'] = document['token_offsets'][multiplicated_subject_nodes[0]]['start']
                    multiplicated_relation['subject']['text_chunk_end_offset'] = document['token_offsets'][multiplicated_subject_nodes[-1]]['end']
                    multiplicated_relation['predicate']['node_ids'] = multiplicated_predicate_nodes
                    multiplicated_relation['predicate']['text_chunk_start_offset'] = document['token_offsets'][multiplicated_predicate_nodes[0]]['start']
                    multiplicated_relation['predicate']['text_chunk_end_offset'] = document['token_offsets'][multiplicated_predicate_nodes[-1]]['end']
                    multiplicated_relation['object']['node_ids'] = multiplicated_object_nodes
                    multiplicated_relation['object']['text_chunk_start_offset'] = document['token_offsets'][multiplicated_object_nodes[0]]['start']
                    multiplicated_relation['object']['text_chunk_end_offset'] = document['token_offsets'][multiplicated_object_nodes[-1]]['end']

                    multiplicated_relations.append(multiplicated_relation)

        # Create json-elayer file.
        json_filename = '{}/{}.json'.format(args.json, document_id)
        json.dump(multiplicated_relations, open(json_filename, 'w'), sort_keys=True, indent=4, separators=(',', ': '))

        # Create pml-elayer file.
        pml_m_filename = '{}/{}.m'.format(args.pml, document_id)
        put_relations_into_m_files(multiplicated_relations, accounting_dictionary, cltt_m_filename, pml_m_filename)
