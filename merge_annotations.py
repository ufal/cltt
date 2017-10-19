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
parser.description = 'Merge two versions of the Brat annotation files into the new one.'
parser.add_argument('--baseline_annotations', required=True, help='directory with ANN files with missing entities and relations')
parser.add_argument('--new_annotations', required=True, help='directory with ANN files with new entities')
# parser.add_argument('--output_dir', required=True, help='directory with the final merged ANN files')
args = parser.parse_args()


# Methods.
def load_annotations(annotation_filename):
    """Return entities and relations as defined in the given file."""

    entities = []
    relations = []
    with open(annotation_filename, 'r') as input_file:
        for line in input_file:
            line = line.rstrip()

            if line[0] == 'T':
                entity_id, annotation, text = line.split('\t')
                entity_type, start_offset, end_offset = annotation.split(' ')
                entities.append({
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'start': start_offset,
                    'end': end_offset,
                    'text': text
                })
            elif line[0] == 'R':
                relation_id, arguments = line.split('\t')
                relation_type, arg1, arg2 = arguments.split(' ')
                arg1 = re.sub(r'Arg1:', '', arg1)
                arg2 = re.sub(r'Arg2:', '', arg2)
                relations.append({
                    'relation_id': relation_id,
                    'relation_type': relation_type,
                    'arg1': arg1,
                    'arg2': arg2
                })
            else:
                logging.warning('Unknown line %s', line)

    return entities, relations


def merge_entities(manual, automatic):
    """Return merged set of entities."""
    merged_entities = []
    for entity in manual:
        if entity['entity_type'] != 'MissingEntity':
            merged_entities.append(entity)
            continue

        automatic_entity = None
        for candidate in automatic:
            if candidate['start'] == entity['start'] and candidate['end'] == entity['end']:
                automatic_entity = candidate
                break

        if automatic_entity:
            merged_entities.append(automatic_entity)
        else:
            logging.warning('Cannot find candidate for %r', entity)

    return merged_entities


# Main.
if __name__ == "__main__":
    filenames = sorted(os.listdir(args.baseline_annotations))
    for filename in filenames:
        if filename[-3:] != 'ann':
            continue

        full_path_baseline = '/'.join([args.baseline_annotations, filename])
        full_path_updated = '/'.join([args.new_annotations, filename])

        baseline_entities, baseline_relations = load_annotations(full_path_baseline)
        new_entities, new_relations = load_annotations(full_path_updated)
        logging.info('%s | E = %5d | R = %5d | | E = %5d | R = %5d', filename, len(baseline_entities),
                     len(baseline_relations), len(new_entities), len(new_relations))

        merge_entities(baseline_entities, new_entities)

