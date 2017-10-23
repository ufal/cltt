#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import os
import logging
import argparse

from cltt.accounting_dictionary import Dictionary
from cltt.btred import load_detected_entities
from cltt.pml import load_m_file, put_entities_into_m_files
from cltt.entities import put_entities_into_json, filter_fragmented_entities, filter_overlapping_entities

# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Add data about detected entities into PML m-files.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--efind', required=True, help='Efind output directory')
parser.add_argument('--cltt', required=True, help='CLTT PML files directory')
parser.add_argument('--pml', required=False, default=None, help='Updated PML files with marked entities.')
parser.add_argument('--brat', required=False, default=None, help='Brat TXT & ANN files with the annotation')
parser.add_argument('--json', required=True, help='Json files with the annotation.')
args = parser.parse_args()


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

        # Load automatically detected entities.
        detected_entities = list()
        btred_files = ['%s/%s' % (args.efind, filename) for filename in sorted(os.listdir(args.efind)) if filename[:len(document_id)] == document_id]
        for n_file, file_name in enumerate(btred_files):
            if (n_file % 1000) == 0:
                logging.info('Loaded %5d efind files.', n_file)
            detected_entities.extend(load_detected_entities(file_name))
        logging.info('Loaded %d entities', len(detected_entities))

        # Filter entities.
        detected_entities = filter_fragmented_entities(detected_entities, document, accounting_dictionary)
        detected_entities = filter_overlapping_entities(detected_entities, document, accounting_dictionary)

        # Different outputs
        json_filename = '%s/%s.json' % (args.json, document_id)
        final_entities = put_entities_into_json(document, detected_entities, accounting_entities, json_filename)

        # if args.brat:
        #     create_plaintext_files(documents, args.brat)
        #     create_annotation_files(documents, node_offsets, entities, accounting_entities, args.brat)

        if args.pml:
            cltt_m_filename_with_entities = '{}/{}.m'.format(args.pml, document_id)
            put_entities_into_m_files(final_entities, accounting_dictionary, cltt_m_filename, cltt_m_filename_with_entities)
