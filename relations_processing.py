#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import re
import os
import json
import logging
import argparse

from cltt.accounting_dictionary import Dictionary
from cltt.pml import load_m_file, put_relations_into_m_files
from cltt.brat import load_ann_file
from cltt.entities import load_detected_entities
from cltt.relations import RelationBuilder


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Merge automatically detected entities with manually detected relations.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--brat', required=True, help='Brat files with manual annotation')
parser.add_argument('--entities', required=True, help='Automatically detected entities')
parser.add_argument('--cltt', required=True, help='CLTT PML files.')
parser.add_argument('--json', required=True, help='Relation description output directory.')
parser.add_argument('--elayer', required=False, default=None, help='PML files with entities annotation.')
parser.add_argument('--rlayer', required=False, default=None, help='PML files with relation annotation.')
# parser.add_argument('--brat', required=False, default=None, help='Brat files output.')
# parser.add_argument('--output_dir', required=True, help='directory with the final merged ANN files')
args = parser.parse_args()


# Main.
if __name__ == "__main__":
    # Accounting Dictionary.
    accounting_dictionary = Dictionary()
    accounting_dictionary.load_json(args.dictionary)
    accounting_entities, entity_types = accounting_dictionary.dictionary, accounting_dictionary.entity_types

    document_ids = [document[:-2] for document in sorted(os.listdir(args.cltt)) if document[-2:] == '.m']
    for document_id in document_ids:
        logging.info('Processing document %s :', document_id)

        # Load PML.
        cltt_m_filename = '{}/{}.m'.format(args.cltt, document_id)
        document = load_m_file(cltt_m_filename)

        # Load manually annotated entities.
        brat_ann_filename = '{}/{}.ann'.format(args.brat, document_id)
        annotated_entities, annotated_relations = load_ann_file(brat_ann_filename)

        # Load automatically detected entities.
        entity_filename = '{}/{}.json'.format(args.entities, document_id)
        detected_entities = load_detected_entities(entity_filename)
        logging.info('Loaded %d automatically detected entities.', len(detected_entities))

        relation_builder = RelationBuilder(annotated_relations, annotated_entities, detected_entities, document)
        relation_builder.align_entities()
        relation_builder.build_relations()
        logging.info('Number of built relations: %d', len(relation_builder.relations))

        json_r_filename = '{}/{}.json'.format(args.json, document_id)
        relation_builder.save_json(json_r_filename)

        if args.elayer:
            input_pml_file = '{}/{}.m'.format(args.elayer, document_id)
            output_pml_file = '{}/{}.m'.format(args.rlayer, document_id)
            put_relations_into_m_files(relation_builder.relations, accounting_dictionary, input_pml_file, output_pml_file)
